"""
IntentAgent - 意图理解

职责：理解用户自然语言输入，识别意图并提取参数。
这是整个流程的入口 Agent。

支持的意图：
- query_assets: 查询资产（"帮我看看钱包里有什么"）
- generate_strategy: 生成策略（"给我推荐一个稳健的DeFi策略"）
- execute_trade: 执行交易（"帮我在Jupiter上把100 SOL换成USDC"）
- risk_check: 风控检查（"这个代币安全吗"）
- chat: 普通聊天（"Solana是什么"）
"""

from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class IntentAgent(BaseAgent):
    name = "intent_agent"
    description = "理解用户意图，提取关键参数"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("intent_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/intent_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """理解用户意图"""
        user_input = state.get("user_input", "")

        if not user_input:
            state["error"] = "用户输入为空"
            return state

        chat_history = state.get("chat_history", [])

        # 调试日志
        print(f"\n{'=' * 60}")
        print(f"[IntentAgent] 用户输入: {user_input}")
        print(f"[IntentAgent] 历史对话数量: {len(chat_history)}")
        if chat_history:
            print("[IntentAgent] 最近3条历史:")
            for msg in chat_history[-3:]:
                print(f"  - {msg.get('role')}: {msg.get('content')[:50]}...")
        print(f"{'=' * 60}\n")

        result = await self.call_llm_json(user_input, chat_history)

        normalized_input = user_input.lower()
        strategy_keywords = [
            "策略",
            "推荐",
            "收益",
            "理财",
            "defi",
            "稳健",
            "保守",
            "年化",
            "apy",
        ]
        should_force_strategy = any(keyword in normalized_input for keyword in strategy_keywords)
        conservative_keywords = ["保守", "稳健", "低风险", "稳一点"]

        if result.get("parse_error"):
            # JSON 解析失败，默认当作普通聊天
            if should_force_strategy:
                state["intent"] = "generate_strategy"
                state["intent_params"] = {
                    "risk_level": (
                        "conservative"
                        if any(keyword in user_input for keyword in conservative_keywords)
                        else "balanced"
                    ),
                    "token": "SOL",
                }
                print("[IntentAgent] ❌ JSON 解析失败，但命中策略关键词，强制识别为 generate_strategy")
            else:
                state["intent"] = "chat"
                state["intent_params"] = {}
                print("[IntentAgent] ❌ JSON 解析失败，默认为 chat")
        else:
            state["intent"] = result.get("intent", "chat")
            state["intent_params"] = result.get("params", {})
            if state["intent"] == "generate_strategy" and any(
                keyword in user_input for keyword in conservative_keywords
            ):
                current_risk = state["intent_params"].get("risk_level")
                if current_risk in (None, "", "balanced", "moderate"):
                    state["intent_params"]["risk_level"] = "conservative"
            if state["intent"] == "chat" and should_force_strategy:
                state["intent"] = "generate_strategy"
                state["intent_params"] = {
                    **state["intent_params"],
                    "risk_level": state["intent_params"].get("risk_level")
                    or (
                        "conservative"
                        if any(keyword in user_input for keyword in conservative_keywords)
                        else "balanced"
                    ),
                    "token": state["intent_params"].get("token", "SOL"),
                }
                print("[IntentAgent] ⚠️ LLM 判成 chat，但命中策略关键词，修正为 generate_strategy")
            print(f"[IntentAgent] ✓ 识别意图: {state['intent']}")
            print(f"[IntentAgent] ✓ 参数: {state['intent_params']}")
            if result.get("reasoning"):
                print(f"[IntentAgent] ✓ 推理: {result.get('reasoning')}")

        state["current_agent"] = self.name
        return state
