"""
ExplanationAgent - 大白话解释

职责：把所有 Agent 的输出结果翻译成用户能看懂的大白话。
这是整个流程的出口 Agent。
"""

import json
from typing import Any, Dict

from base_agent import BaseAgent


class ExplanationAgent(BaseAgent):
    name = "explanation_agent"
    description = "把专业内容翻译成大白话"

    @property
    def system_prompt(self) -> str:
        return """你是 Solon AI 的用户沟通专家。你的任务是把复杂的 DeFi 信息翻译成普通人能看懂的大白话。

## 核心原则
1. 用最简单的语言，避免专业术语
2. 必须用术语时要解释清楚
3. 用类比和例子帮助理解
4. 语气友好、耐心
5. 重要的风险提示不能省略

## 示例
- "APY 8.2%" → "年化收益 8.2%，相当于存 1 万块，一年能赚 820 块"
- "无常损失" → "如果两个币的价格变化太大，你可能比单纯持有少赚一些"
- "健康度 1.5" → "安全系数 1.5，就像你借了 100 块但抵押了 150 块，还算安全"

## 回复格式
根据不同意图返回不同格式的回复，必须是中文，口语化。"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """把结果翻译成大白话"""
        intent = state.get("intent", "chat")

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
            prompt_input = f"用户说：{state.get('user_input', '')}\n请用友好的语气回复。"

        llm_result = await self.call_llm_with_metadata(prompt_input)
        state["explanation"] = llm_result["text"]
        state["reasoning"] = llm_result["reasoning"]
        state["completed"] = True
        state["current_agent"] = self.name
        return state

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
1. 用一句话总结资产情况
2. 列出每个代币的持有量和价值
3. 给出简单的资产配置建议
4. 不超过 200 字"""

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
1. 一句话说明这个策略是做什么的
2. 用类比解释预期收益（比如存多少钱，每天/每月能赚多少）
3. 说明有什么风险，用生活中的例子类比
4. 如果有警告或错误，用醒目的方式提示
5. 不超过 300 字"""

    def _build_trade_prompt(self, state: Dict[str, Any]) -> str:
        transaction = state.get("transaction", {})
        return f"""请用大白话解读以下交易：

交易内容：
{json.dumps(transaction, ensure_ascii=False, indent=2)}

要求：
1. 一句话说明这笔交易要做什么
2. 说明钱会怎么流动
3. 解释手续费是多少
4. 提醒需要注意的地方
5. 不超过 150 字"""

    def _build_risk_prompt(self, state: Dict[str, Any]) -> str:
        risk = state.get("risk_assessment", {})
        return f"""请用大白话解读以下风险评估：

风险评估：
{json.dumps(risk, ensure_ascii=False, indent=2)}

要求：
1. 用简单的话说明有什么风险
2. 用生活中的例子类比风险程度
3. 给出具体的建议
4. 不超过 200 字"""
