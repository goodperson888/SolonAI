"""
ExplanationAgent - 大白话解释

职责：把所有 Agent 的输出结果翻译成用户能看懂的大白话。
这是整个流程的出口 Agent。
使用 RAG 知识库为回复提供事实性参考知识。
"""

import json
import logging
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt

logger = logging.getLogger(__name__)


def _retrieve_rag_context(query: str, wallet_address: str = None) -> dict:
    """从 RAG 知识库检索相关知识，失败时静默返回空

    Returns:
        dict: {"context": str, "sources": [{"filename": str, "source": str}]}
    """
    try:
        logger.info(f"[RAG] 开始检索知识，查询: {query}, 钱包: {wallet_address}")

        # 如果有钱包地址，从用户上传的文档中检索
        if wallet_address:
            try:
                from rag.user_knowledge import retrieve_user_knowledge_with_sources

                result = retrieve_user_knowledge_with_sources(wallet_address, query, top_k=3)
                logger.info(f"[RAG] 用户知识库检索结果: {len(result.get('sources', []))} 个来源")
                if result.get("context"):
                    return result
            except Exception as e:
                logger.warning(f"[RAG] 用户知识库检索失败: {e}")

        # 降级到系统知识库
        from rag.knowledge_base import retrieve_knowledge

        result = retrieve_knowledge(query, top_k=3)
        logger.info(f"[RAG] 系统知识库检索结果长度: {len(result)}")
        return {"context": result, "sources": []}
    except Exception as e:
        logger.warning(f"[RAG] 知识检索失败: {e}", exc_info=True)
        return {"context": "", "sources": []}


class ExplanationAgent(BaseAgent):
    name = "explanation_agent"
    description = "把专业内容翻译成大白话"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("explanation_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/explanation_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """把结果翻译成大白话（结合 RAG 知识库）"""
        intent = state.get("intent", "chat")
        user_input = state.get("user_input", "")
        wallet_address = state.get("wallet_address", "")

        # 根据不同意图构建不同的输入
        if intent == "query_assets":
            prompt_input = self._build_assets_prompt(state)
        elif intent == "generate_strategy":
            prompt_input = self._build_strategy_prompt(state)
        elif intent == "execute_trade":
            prompt_input = self._build_trade_prompt(state)
        elif intent == "risk_check":
            prompt_input = self._build_risk_prompt(state)
        else:
            # 普通聊天 - 如果有 DeFi 数据或钱包资产，也提供给 AI 参考
            best_opportunities = state.get("defi_best_opportunities", [])
            market_prices = state.get("market_prices", {})
            wallet_assets = state.get("wallet_assets", [])
            total_value_usd = state.get("total_value_usd", 0)

            # 构建可用数据
            available_data = []
            if wallet_assets:
                available_data.append(
                    f"- 用户资产：{json.dumps(wallet_assets, ensure_ascii=False)} (总价值: ${total_value_usd:.2f})"
                )
            if best_opportunities:
                available_data.append(
                    f"- 最佳收益机会：{json.dumps(best_opportunities[:5], ensure_ascii=False)}"
                )
            if market_prices:
                available_data.append(
                    f"- 市场价格：{json.dumps(market_prices, ensure_ascii=False)}"
                )

            if available_data:
                prompt_input = f"""用户说：{user_input}

可用的数据（供参考）：
{chr(10).join(available_data)}

请用友好的语气回复用户的问题。如果问题与资产、DeFi 收益、价格相关，可以引用上述数据。"""
            else:
                prompt_input = f"用户说：{user_input}\n请用友好的语气回复。"

        # 从 RAG 知识库检索相关知识作为参考
        logger.info(
            f"[ExplanationAgent] 准备检索 RAG，用户输入: {user_input}, 钱包: {wallet_address}"
        )
        rag_result = _retrieve_rag_context(user_input, wallet_address)
        rag_context = rag_result.get("context", "")
        rag_sources = rag_result.get("sources", [])
        if rag_context:
            logger.info(f"[ExplanationAgent] RAG 上下文已添加，长度: {len(rag_context)}")
            prompt_input = f"{rag_context}\n\n---\n\n{prompt_input}"
        else:
            logger.info("[ExplanationAgent] 未检索到 RAG 上下文")

        llm_result = await self.call_llm_with_metadata(prompt_input, state.get("chat_history", []))
        state["explanation"] = llm_result["text"]
        state["reasoning"] = llm_result["reasoning"]
        state["rag_sources"] = rag_sources
        state["completed"] = True
        state["current_agent"] = self.name
        return state

    async def process_stream(self, state: Dict[str, Any]):
        """
        流式版本的 process()，逐字生成回复

        Yields:
            str: 每个生成的 token

        最后 yield 完整的 state
        """
        intent = state.get("intent", "chat")
        user_input = state.get("user_input", "")
        wallet_address = state.get("wallet_address", "")

        # 根据不同意图构建不同的输入
        if intent == "query_assets":
            prompt_input = self._build_assets_prompt(state)
        elif intent == "generate_strategy":
            prompt_input = self._build_strategy_prompt(state)
        elif intent == "execute_trade":
            prompt_input = self._build_trade_prompt(state)
        elif intent == "risk_check":
            prompt_input = self._build_risk_prompt(state)
        else:
            # 普通聊天 - 如果有 DeFi 数据或钱包资产，也提供给 AI 参考
            best_opportunities = state.get("defi_best_opportunities", [])
            market_prices = state.get("market_prices", {})
            wallet_assets = state.get("wallet_assets", [])
            total_value_usd = state.get("total_value_usd", 0)

            # 构建可用数据
            available_data = []
            if wallet_assets:
                available_data.append(
                    f"- 用户资产：{json.dumps(wallet_assets, ensure_ascii=False)} (总价值: ${total_value_usd:.2f})"
                )
            if best_opportunities:
                available_data.append(
                    f"- 最佳收益机会：{json.dumps(best_opportunities[:5], ensure_ascii=False)}"
                )
            if market_prices:
                available_data.append(
                    f"- 市场价格：{json.dumps(market_prices, ensure_ascii=False)}"
                )

            if available_data:
                prompt_input = f"""用户说：{user_input}

可用的数据（供参考）：
{chr(10).join(available_data)}

请用友好的语气回复用户的问题。如果问题与资产、DeFi 收益、价格相关，可以引用上述数据。"""
            else:
                prompt_input = f"用户说：{user_input}\n请用友好的语气回复。"

        # 优先使用 chat.py 预检索的 RAG 上下文（避免 Agent 自调用 HTTP 死锁）
        rag_context = state.get("rag_context", "")
        if rag_context:
            logger.info(f"[ExplanationAgent] 使用预检索的 RAG 上下文，长度: {len(rag_context)}")
            prompt_input = f"{rag_context}\n\n---\n\n{prompt_input}"
        else:
            # 降级：Agent 自己检索（非 HTTP 自调用场景下可用）
            logger.info(f"[ExplanationAgent] 尝试自行检索 RAG，钱包: {wallet_address}")
            rag_result = _retrieve_rag_context(user_input, wallet_address)
            ctx = rag_result.get("context", "")
            if ctx:
                logger.info(f"[ExplanationAgent] RAG 上下文已添加，长度: {len(ctx)}")
                prompt_input = f"{ctx}\n\n---\n\n{prompt_input}"
            else:
                logger.info("[ExplanationAgent] 未检索到 RAG 上下文")

        # 流式调用 LLM
        full_text = ""
        async for token in self.call_llm_stream(prompt_input, state.get("chat_history", [])):
            full_text += token
            yield token

        # 更新状态
        state["explanation"] = full_text
        state["completed"] = True
        state["current_agent"] = self.name

    def _build_assets_prompt(self, state: Dict[str, Any]) -> str:
        assets = state.get("wallet_assets", [])
        total = state.get("total_value_usd", 0)
        print(f"[ExplanationAgent] 收到的 state keys: {state.keys()}")
        print(f"[ExplanationAgent] wallet_assets: {assets}")
        print(f"[ExplanationAgent] total_value_usd: {total}")
        return f"""请用大白话解读以下资产情况：

钱包总价值：${total:,.2f}
持有代币：
{json.dumps(assets, ensure_ascii=False, indent=2)}

要求：
1. 按照"查询资产"的格式模板回复
2. 用一句话总结资产情况
3. 列出每个代币的持有量和价值
4. 给出简单的资产配置建议（1-2句话）
5. 控制在 150-200 字"""

    def _build_strategy_prompt(self, state: Dict[str, Any]) -> str:
        # 优先使用 DeFi 聚合数据（DataAggregationAgent 提供）
        best_opportunities = state.get("defi_best_opportunities", [])
        protocol_data = state.get("protocol_data", {})
        market_prices = state.get("market_prices", {})
        wallet_assets = state.get("wallet_assets", [])
        total_value_usd = state.get("total_value_usd", 0)

        # 降级：使用旧的策略数据（如果有专门的 StrategyAgent）
        strategy = state.get("strategy", {})
        risk = state.get("risk_assessment", {})

        if best_opportunities or protocol_data:
            # 构建用户资产信息
            assets_info = ""
            if wallet_assets:
                assets_info = f"""
用户当前资产：
{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}
总价值：${total_value_usd:.2f}
"""
            else:
                assets_info = "用户未连接钱包，无法获取资产信息。"

            # 使用 DeFi 聚合数据
            return f"""请根据以下 DeFi 市场数据和用户资产，为用户推荐投资策略：

{assets_info}

最佳收益机会：
{json.dumps(best_opportunities, ensure_ascii=False, indent=2)}

协议收益率数据：
{json.dumps(protocol_data, ensure_ascii=False, indent=2)}

市场价格：
{json.dumps(market_prices, ensure_ascii=False, indent=2)}

用户参数：
- 风险偏好：{state.get("intent_params", {}).get("risk_level", "moderate")}
- 投资金额：{state.get("intent_params", {}).get("amount", "未指定")}
- 投资币种：{state.get("intent_params", {}).get("token", "SOL")}

要求：
1. **首先告诉用户他当前有多少资产**（如果有资产数据）
2. 从最佳机会中挑选 2-3 个适合用户风险偏好的协议
3. 用大白话解释每个协议是做什么的（比如"像银行存款一样赚利息"）
4. 根据用户实际资产，说明预期收益（比如"你有 40 SOL，存入 MarginFi 一年能赚 2.4 SOL"）
5. 提醒风险（比如"价格波动可能导致损失"）
6. 给出具体操作建议（比如"可以先存一小部分试试"）
7. 控制在 300-400 字"""
        else:
            # 降级：使用旧的策略数据格式
            return f"""请用大白话解读以下投资策略：

策略内容：
{json.dumps(strategy, ensure_ascii=False, indent=2)}

风控审计结果：
{json.dumps(risk, ensure_ascii=False, indent=2)}

要求：
1. 按照"生成策略"的格式模板回复
2. 一句话说明这个策略是做什么的
3. 用类比解释预期收益（比如存多少钱，每天/每月能赚多少）
4. 说明有什么风险，用生活中的例子类比
5. 如果有警告或错误，用醒目的方式提示
6. 控制在 250-300 字"""

    def _build_trade_prompt(self, state: Dict[str, Any]) -> str:
        transaction = state.get("transaction", {})
        return f"""请用大白话解读以下交易：

交易内容：
{json.dumps(transaction, ensure_ascii=False, indent=2)}

要求：
1. 按照"执行交易"的格式模板回复
2. 一句话说明这笔交易要做什么
3. 说明钱会怎么流动
4. 解释手续费是多少
5. 提醒需要注意的地方
6. 控制在 100-150 字"""

    def _build_risk_prompt(self, state: Dict[str, Any]) -> str:
        risk = state.get("risk_assessment", {})
        return f"""请用大白话解读以下风险评估：

风险评估：
{json.dumps(risk, ensure_ascii=False, indent=2)}

要求：
1. 按照"风控检查"的格式模板回复
2. 用简单的话说明有什么风险
3. 用生活中的例子类比风险程度
4. 给出具体的建议
5. 控制在 150-200 字"""
