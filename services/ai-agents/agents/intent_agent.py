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


class IntentAgent(BaseAgent):
    name = "intent_agent"
    description = "理解用户意图，提取关键参数"

    @property
    def system_prompt(self) -> str:
        return """你是 Solon AI 的意图理解模块，负责分析用户输入的自然语言。

你必须识别用户的意图，并提取关键参数。

## 支持的意图类型

1. `query_assets` - 查询资产
   - 用户想查看钱包余额、资产列表、持仓情况
   - 示例："帮我看看钱包里有什么"、"我有多少SOL"

2. `generate_strategy` - 生成投资策略
   - 用户想获取DeFi投资建议
   - 示例："给我推荐一个稳健策略"、"怎么用100 SOL赚利息"
   - 提取参数：risk_level(conservative/moderate/aggressive)、amount、token

3. `execute_trade` - 执行交易
   - 用户想进行代币交换、存款、借贷等操作
   - 示例："把50 SOL换成USDC"、"在MarginFi存入100 USDC"
   - 提取参数：action(swap/deposit/withdraw/borrow)、token_in、token_out、amount

4. `risk_check` - 风控检查
   - 用户想检查某个代币或协议的安全性
   - 示例："这个代币安全吗"、"帮我检查一下授权"
   - 提取参数：target(代币地址或协议名)

5. `chat` - 普通对话
   - 用户在闲聊或问DeFi知识
   - 示例："什么是无常损失"、"Solana和以太坊有什么区别"

## 返回格式

必须返回 JSON：
```json
{
  "intent": "意图类型",
  "confidence": 0.95,
  "params": {
    "risk_level": "conservative",
    "amount": 100,
    "token": "SOL"
  },
  "reasoning": "简短解释为什么判断为这个意��"
}
```"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """理解用户意图"""
        user_input = state.get("user_input", "")

        if not user_input:
            state["error"] = "用户输入为空"
            return state

        result = await self.call_llm_json(user_input)

        if result.get("parse_error"):
            # JSON 解析失败，默认当作普通聊天
            state["intent"] = "chat"
            state["intent_params"] = {}
        else:
            state["intent"] = result.get("intent", "chat")
            state["intent_params"] = result.get("params", {})

        state["current_agent"] = self.name
        return state
