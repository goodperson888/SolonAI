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

logger = logging.getLogger(__name__)


def _retrieve_rag_context(query: str, wallet_address: str = None) -> str:
    """从 RAG 知识库检索相关知识，失败时静默返回空"""
    try:
        logger.info(f"[RAG] 开始检索知识，查询: {query}, 钱包: {wallet_address}")

        # 如果有钱包地址，从用户上传的文档中检索
        if wallet_address:
            try:
                from rag.user_knowledge import retrieve_user_knowledge

                result = retrieve_user_knowledge(wallet_address, query, top_k=3)
                logger.info(f"[RAG] 用户知识库检索结果长度: {len(result)}")
                if result:
                    logger.info(f"[RAG] 检索到的内容预览: {result[:200]}...")
                    return result
            except Exception as e:
                logger.warning(f"[RAG] 用户知识库检索失败: {e}")

        # 降级到系统知识库
        from rag.knowledge_base import retrieve_knowledge

        result = retrieve_knowledge(query, top_k=3)
        logger.info(f"[RAG] 系统知识库检索结果长度: {len(result)}")
        return result
    except Exception as e:
        logger.warning(f"[RAG] 知识检索失败: {e}", exc_info=True)
        return ""


class ExplanationAgent(BaseAgent):
    name = "explanation_agent"
    description = "把专业内容翻译成大白话"

    @property
    def system_prompt(self) -> str:
        return """你是 Solon AI 的用户沟通专家。你的任务是把复杂的 DeFi 信息翻译成普通人能看懂的大白话。

## 核心原则
1. **简单易懂**：用最简单的语言，避免专业术语
2. **必要解释**：必须用术语时要解释清楚
3. **类比举例**：用生活中的例子帮助理解
4. **友好耐心**：语气友好、耐心，像朋友聊天
5. **风险提示**：重要的风险提示不能省略，但不要吓唬用户
6. **数据可视化**：用表格、列表等方式让数据更清晰

## 语言风格
- ✅ "你现在有 227 个 SOL，大概值 4 万美元"
- ❌ "您的钱包地址持有 227.55 SOL，按当前市场价格计算约为 40,576 USD"

- ✅ "年化收益 8.2%，相当于存 1 万块，一年能赚 820 块"
- ❌ "APY 为 8.2%"

- ✅ "如果两个币的价格变化太大，你可能比单纯持有少赚一些，这叫无常损失"
- ❌ "存在无常损失风险"

- ✅ "安全系数 1.5，就像你借了 100 块但抵押了 150 块，还算安全"
- ❌ "健康度因子为 1.5"

## 回复格式要求

### 查询资产 (query_assets)
```
📊 你的资产情况

总价值：$XX,XXX（约 XX 万人民币）

持有代币：
• SOL：XXX 个，价值 $XX,XXX
• USDC：XXX 个，价值 $XXX

💡 小建议：
[根据资产情况给出 1-2 句简单建议]
```

### 生成策略 (generate_strategy)
```
💰 投资策略建议

策略类型：[稳健型/平衡型/激进型]

具体方案：
1. [第一步做什么]
2. [第二步做什么]
3. [第三步做什么]

预期收益：
• 年化收益：XX%
• 举例：投入 1 万块，一年大概能赚 XXX 块

⚠️ 风险提示：
[用生活中的例子说明风险]

是否需要我帮你执行这个策略？
```

### 执行交易 (execute_trade)
```
💸 交易确认

操作：[把 XX SOL 换成 USDC]

交易详情：
• 你支付：XX SOL（约 $XXX）
• 你收到：约 XXX USDC
• 手续费：约 $X.XX

⚠️ 注意事项：
[需要注意的地方]

确认后我会帮你执行，是否继续？
```

### 风控检查 (risk_check)
```
🔍 安全检查结果

检查对象：[代币名称/协议名称]

安全评分：⭐⭐⭐⭐☆ (4/5)

详细说明：
• [安全的地方]
• [需要注意的地方]

💡 建议：
[具体的操作建议]
```

### 普通对话 (chat)
```
[用友好、口语化的方式回答问题]

如果是知识类问题：
1. 用一句话说明核心概念
2. 用生活中的例子类比
3. 如果有相关操作，可以引导用户

如果是打招呼：
简短友好地回应，可以介绍自己能做什么
```

## 数字格式化规则
- 金额 > 10000：用"万"表示，如"4 万美元"
- 金额 < 10000：直接显示，如"$8,520"
- 百分比：保留 1 位小数，如"8.2%"
- 代币数量：根据大小决定小数位
  - > 100：保留 2 位小数
  - 1-100：保留 4 位小数
  - < 1：保留 6 位小数

## 特殊情况处理

1. **数据为空或错误**
   - 不要说"查询失败"、"数据为空"
   - 改为"暂时没查到数据，可能是网络问题，要不要重试一下？"

2. **高风险操作**
   - 用醒目的 ⚠️ 标记
   - 说明具体风险，不要只说"有风险"
   - 给出降低风险的建议

3. **复杂概念**
   - 先用一句话总结
   - 再用类比解释
   - 最后给出实际例子

4. **多个选项**
   - 用表格或列表对比
   - 标注推荐项
   - 说明推荐理由

## 禁止事项
❌ 不要使用：APY、TVL、LP、健康度、清算线等专业术语（除非解释）
❌ 不要使用：您、阁下等过于正式的称呼
❌ 不要使用：建议您谨慎操作等官方套话
❌ 不要过度使用 emoji（每段最多 1-2 个）
❌ 不要给出具体的投资建议（"一定会赚"、"保证收益"等）

## 回复长度控制
- 查询资产：150-200 字
- 生成策略：250-300 字
- 执行交易：100-150 字
- 风控检查：150-200 字
- 普通对话：根据问题复杂度，50-200 字"""

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
            # 普通聊天
            prompt_input = f"用户说：{user_input}\n请用友好的语气回复。"

        # 从 RAG 知识库检索相关知识作为参考
        logger.info(
            f"[ExplanationAgent] 准备检索 RAG，用户输入: {user_input}, 钱包: {wallet_address}"
        )
        rag_context = _retrieve_rag_context(user_input, wallet_address)
        if rag_context:
            logger.info(f"[ExplanationAgent] RAG 上下文已添加，长度: {len(rag_context)}")
            prompt_input = f"{rag_context}\n\n---\n\n{prompt_input}"
        else:
            logger.info("[ExplanationAgent] 未检索到 RAG 上下文")

        llm_result = await self.call_llm_with_metadata(prompt_input, state.get("chat_history", []))
        state["explanation"] = llm_result["text"]
        state["reasoning"] = llm_result["reasoning"]
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
            # 普通聊天
            prompt_input = f"用户说：{user_input}\n请用友好的语气回复。"

        # 从 RAG 知识库检索相关知识作为参考
        logger.info(
            f"[ExplanationAgent] 准备检索 RAG，用户输入: {user_input}, 钱包: {wallet_address}"
        )
        rag_context = _retrieve_rag_context(user_input, wallet_address)
        if rag_context:
            logger.info(f"[ExplanationAgent] RAG 上下文已添加，长度: {len(rag_context)}")
            prompt_input = f"{rag_context}\n\n---\n\n{prompt_input}"
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
        strategy = state.get("strategy", {})
        risk = state.get("risk_assessment", {})
        validation = state.get("validation_result", {})
        return f"""请用大白话解读以下投资策略：

策略内容：
{json.dumps(strategy, ensure_ascii=False, indent=2)}

风控审计结果：
{json.dumps(risk, ensure_ascii=False, indent=2)}

验证结果：
{json.dumps(validation, ensure_ascii=False, indent=2)}

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
