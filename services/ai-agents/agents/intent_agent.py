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
        result = await self.call_llm_json(user_input, chat_history)

        if result.get("parse_error"):
            # JSON 解析失败，默认当作普通聊天
            state["intent"] = "chat"
            state["intent_params"] = {}
        else:
            state["intent"] = result.get("intent", "chat")
            state["intent_params"] = result.get("params", {})

        state["current_agent"] = self.name
        return state
