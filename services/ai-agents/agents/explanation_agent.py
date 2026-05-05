"""
ExplanationAgent - 大白话解释

职责：把所有 Agent 的输出结果翻译成用户能看懂的大白话。
这是整个流程的出口 Agent。
使用 RAG 知识库为回复提供事实性参考知识。
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from base_agent import BaseAgent
from prompts import get_prompt

logger = logging.getLogger(__name__)


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def _is_greeting(text: str) -> bool:
    normalized = _normalize_text(text)
    return normalized in {"你好", "您好", "hi", "hello", "hey", "嗨", "哈喽"}


def _is_identity_question(text: str) -> bool:
    normalized = _normalize_text(text)
    return normalized in {"你是谁", "你是誰", "whoareyou", "介绍一下你自己", "你能做什么"}


def _extract_price_symbol(text: str) -> Optional[str]:
    raw = (text or "").upper()
    for symbol in ["BTC", "ETH", "SOL", "USDC", "USDT", "JUP", "RAY", "BONK"]:
        if symbol in raw:
            return symbol
    return None


def _is_price_question(text: str) -> bool:
    raw = (text or "").lower()
    keywords = ["价格", "多少钱", "price", "quote", "行情", "市价"]
    return any(keyword in raw for keyword in keywords) and _extract_price_symbol(text) is not None


def _build_direct_chat_reply(state: Dict[str, Any]) -> Optional[str]:
    user_input = state.get("user_input", "")
    is_chinese = _contains_cjk(user_input)

    if _is_greeting(user_input):
        return (
            "你好，我是 Solon AI。你可以让我帮你看资产、做策略、看风险，或者解释 Solana / DeFi 问题。"
            if is_chinese
            else "Hi, I'm Solon AI. I can help with assets, strategies, risk checks, and Solana/DeFi questions."
        )

    if _is_identity_question(user_input):
        return (
            "我是 Solon AI，专门帮你做 Solana 生态里的资产查看、DeFi 策略建议、执行前确认和风险提示。"
            if is_chinese
            else "I'm Solon AI. I help with Solana asset views, DeFi strategy ideas, execution previews, and risk checks."
        )

    if _is_price_question(user_input):
        symbol = _extract_price_symbol(user_input) or "该代币"
        market_prices = state.get("market_prices", {}) or {}
        price_entry = market_prices.get(symbol)
        price_value = price_entry.get("price_usd") if isinstance(price_entry, dict) else None
        if isinstance(price_value, (int, float)):
            return (
                f"{symbol} 当前参考价格约为 ${price_value:.2f}。如果你愿意，我也可以顺手结合你的钱包资产看一下它对你的仓位影响。"
                if is_chinese
                else f"{symbol} is currently around ${price_value:.2f}. If you want, I can also relate that to your wallet holdings."
            )
        return (
            f"我现在没有 {symbol} 的实时价格数据源，所以不想乱报一个数字给你。要是你愿意，我可以先帮你接一个更完整的行情源，或者继续回答它的用途和风险。"
            if is_chinese
            else f"I don't have a live price source for {symbol} right now, so I don't want to guess. I can help wire in a market feed or explain its use and risks instead."
        )

    return None


def _infer_protocol_from_strategy(strategy: Optional[Dict[str, Any]]) -> str:
    if not strategy:
        return ""

    protocol = strategy.get("protocol") or strategy.get("protocol_name")
    if isinstance(protocol, str) and protocol.strip():
        return protocol.strip().lower()

    for step in strategy.get("steps", []) or []:
        step_protocol = step.get("protocol")
        if isinstance(step_protocol, str) and step_protocol.strip():
            return step_protocol.strip().lower()

    for protocol_name in strategy.get("protocols", []) or []:
        if isinstance(protocol_name, str) and protocol_name.strip():
            return protocol_name.strip().lower()

    return ""


def _is_lending_like_strategy(strategy: Optional[Dict[str, Any]]) -> bool:
    if not strategy:
        return False

    protocol = _infer_protocol_from_strategy(strategy)
    if protocol in {"marginfi", "solend", "kamino"}:
        return True

    steps = strategy.get("steps", []) or []
    normalized_actions = {str(step.get("action") or "").strip().lower() for step in steps}
    normalized_actions.discard("")
    if not normalized_actions:
        return False

    return normalized_actions.issubset({"deposit", "lend", "supply", "stake"})


def _sanitize_risk_assessment(
    risk_assessment: Optional[Dict[str, Any]],
    strategy: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    sanitized = dict(risk_assessment or {})
    warnings = sanitized.get("warnings") or []

    if _is_lending_like_strategy(strategy):
        warnings = [
            warning
            for warning in warnings
            if "无常损失" not in str(warning)
        ]

    sanitized["warnings"] = warnings
    return sanitized


def _sanitize_protocol_mentions(text: str, allowed_protocols: set[str]) -> str:
    if not text:
        return text

    blocked_protocols = {
        "lido": "未知外部协议",
        "uniswap": "未知外部协议",
        "marinade": "其他质押协议",
        "aave": "其他借贷协议",
    }

    sanitized = text
    lowered = {item.lower() for item in allowed_protocols if item}
    for protocol, replacement in blocked_protocols.items():
        if protocol not in lowered:
            sanitized = re.sub(protocol, replacement, sanitized, flags=re.IGNORECASE)
    return sanitized


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
        direct_reply = _build_direct_chat_reply(state)
        if direct_reply and intent == "chat":
            state["explanation"] = direct_reply
            state["reasoning"] = "direct_chat_template"
            state["rag_sources"] = []
            state["completed"] = True
            state["current_agent"] = self.name
            return state

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
            prompt_input = self._build_general_chat_prompt(state)

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
        allowed_protocols = {
            str(item).strip()
            for item in (
                list((state.get("strategy") or {}).get("protocols", []) or [])
                + [state.get("strategy", {}).get("protocol")]
                + [state.get("strategy", {}).get("protocol_name")]
                + list((state.get("protocol_data") or {}).keys())
            )
            if item
        }
        state["explanation"] = _sanitize_protocol_mentions(llm_result["text"], allowed_protocols)
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
        direct_reply = _build_direct_chat_reply(state)
        if direct_reply and intent == "chat":
            for char in direct_reply:
                yield char
            state["explanation"] = direct_reply
            state["completed"] = True
            state["current_agent"] = self.name
            return

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
            prompt_input = self._build_general_chat_prompt(state)

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
        allowed_protocols = {
            str(item).strip()
            for item in (
                list((state.get("strategy") or {}).get("protocols", []) or [])
                + [state.get("strategy", {}).get("protocol")]
                + [state.get("strategy", {}).get("protocol_name")]
                + list((state.get("protocol_data") or {}).keys())
            )
            if item
        }
        state["explanation"] = _sanitize_protocol_mentions(full_text, allowed_protocols)
        state["completed"] = True
        state["current_agent"] = self.name

    def _build_assets_prompt(self, state: Dict[str, Any]) -> str:
        assets = state.get("wallet_assets", [])
        total = state.get("total_value_usd", 0)
        has_non_zero_assets = any(float(asset.get("balance", 0) or 0) > 0 for asset in assets)
        print(f"[ExplanationAgent] 收到的 state keys: {state.keys()}")
        print(f"[ExplanationAgent] wallet_assets: {assets}")
        print(f"[ExplanationAgent] total_value_usd: {total}")
        if assets and has_non_zero_assets and float(total or 0) <= 0:
            total_line = "钱包总价值：暂时无法准确估算（价格数据未取回）"
        else:
            total_line = f"钱包总价值：${total:,.2f}"
        return f"""请用大白话解读以下资产情况：

{total_line}
持有代币：
{json.dumps(assets, ensure_ascii=False, indent=2)}

要求：
1. 按照"查询资产"的格式模板回复
2. 用一句话总结资产情况
3. 列出每个代币的持有量和价值；如果某个代币或总价值暂无估值，就明确写“估值暂时不可用”，不要写成 $0.00，也不要说资产为空
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
        risk = _sanitize_risk_assessment(state.get("risk_assessment", {}), strategy)

        has_non_zero_assets = any(float(asset.get("balance", 0) or 0) > 0 for asset in wallet_assets)
        if wallet_assets:
            if has_non_zero_assets and float(total_value_usd or 0) <= 0:
                assets_info = (
                    f"用户当前资产：\n{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}\n"
                    "总价值暂时无法准确估算（价格数据未取回），但用户确实持有以上资产。\n"
                )
            else:
                assets_info = (
                    f"用户当前资产：\n{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}\n"
                    f"总价值：${total_value_usd:.2f}\n"
                )
        else:
            assets_info = "用户未连接钱包，无法获取资产信息。\n"

        market_context = ""
        if best_opportunities or protocol_data or market_prices:
            market_context = f"""
可参考的市场信息：
- 最佳收益机会：{json.dumps(best_opportunities[:3], ensure_ascii=False, indent=2)}
- 协议收益率数据：{json.dumps(protocol_data, ensure_ascii=False, indent=2)}
- 市场价格：{json.dumps(market_prices, ensure_ascii=False, indent=2)}
"""

        return f"""请把“已经生成好的这套策略”解释给用户听，不要重新推荐另一套完全不同的方案。

{assets_info}

策略内容：
{json.dumps(strategy, ensure_ascii=False, indent=2)}

风控审计结果：
{json.dumps(risk, ensure_ascii=False, indent=2)}

{market_context}

用户参数：
- 风险偏好：{state.get("intent_params", {}).get("risk_level", "balanced")}
- 投资金额：{state.get("intent_params", {}).get("amount", "未指定")}
- 投资币种：{state.get("intent_params", {}).get("token", "SOL")}

要求：
1. 必须优先解释上面这套现有策略，不能再额外推荐 2-3 个新协议。
2. 开头先明确用户当前真实资产，严禁虚构 40 SOL 这类持仓。
3. 如果用户钱包里有非零资产，但总价值是 0 或缺失，只能说“价格估值暂不可用”，绝对不能说“没有资产”。
4. 用 4 个短部分回答，标题固定为：
   `资产情况`
   `推荐策略`
   `主要风险`
   `执行建议`
5. `推荐策略` 里只解释当前策略的核心协议、预期收益和步骤，不要展开成很多分散选项。
6. `执行建议` 必须给出可操作动作，例如“先保存到策略工作台，再点击执行”或“先用模拟模式验证”。
7. 如果举收益例子，必须直接基于当前真实资产估算。
8. 语言尽量像产品文案，简洁、可信、可执行，不要写成长篇散文。
9. 控制在 220-320 字。"""

    def _build_general_chat_prompt(self, state: Dict[str, Any]) -> str:
        user_input = state.get("user_input", "")
        market_prices = state.get("market_prices", {})

        if _is_price_question(user_input):
            return f"""用户问题：{user_input}

可用市场价格数据：
{json.dumps(market_prices, ensure_ascii=False, indent=2)}

要求：
1. 只回答用户问到的价格问题，不要主动扯回钱包资产或投资策略。
2. 如果提供的数据里没有对应币种价格，就明确说当前没有该币种实时价格，不要编造。
3. 不要推荐 Lido、Uniswap、Aave、Ethereum 生态协议，除非用户明确点名。
4. 语言简洁，控制在 80-140 字。"""

        return f"""用户说：{user_input}

要求：
1. 如果这是打招呼、自我介绍或普通知识问答，就直接回答当前问题。
2. 不要主动引入钱包资产、投资建议、收益方案，除非用户明确在问这些。
3. 不要编造任何协议名、收益率或价格。
4. 不要推荐 Lido、Uniswap、Aave、Ethereum 生态协议，除非用户明确点名。
5. 语气友好自然，控制在 60-180 字。"""

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
