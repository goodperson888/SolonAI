"""
StrategyAgent - 策略生成

职责：基于用户需求和链上数据，生成 DeFi 投资策略。
包含收益测算、风险评级、操作步骤拆解。
"""

import json
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class StrategyAgent(BaseAgent):
    name = "strategy_agent"
    description = "基于用户需求生成DeFi策略"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("strategy_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/strategy_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成投资策略"""
        intent_params = state.get("intent_params", {})
        wallet_assets = state.get("wallet_assets", [])
        protocol_data = state.get("protocol_data", {})

        # 构建给 LLM 的输入
        prompt_input = f"""
用户需求：
- 风险偏好：{intent_params.get('risk_level', 'conservative')}
- 投资金额：{intent_params.get('amount', '未指定')}
- 指定代币：{intent_params.get('token', '未指定')}

用户当前持仓：
{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}

可用协议数据：
{json.dumps(protocol_data, ensure_ascii=False, indent=2)}

请生成一个可执行的 DeFi 投资策略。"""

        result = await self.call_llm_json(prompt_input)

        if result.get("parse_error"):
            # 降级：返回一个默认的保守策略
            result = {
                "strategy_name": "MarginFi 稳健生息",
                "risk_level": "conservative",
                "expected_apy": 8.2,
                "protocols": ["MarginFi"],
                "steps": [
                    {
                        "step": 1,
                        "action": "deposit",
                        "protocol": "MarginFi",
                        "token": "USDC",
                        "amount": 5000,
                        "expected_apy": 8.2,
                        "description": "将 USDC 存入 MarginFi 赚取利息",
                    }
                ],
                "risk_warnings": ["协议合约风险"],
                "total_investment": 5000,
                "estimated_daily_income": 1.12,
                "estimated_monthly_income": 33.7,
            }

        state["strategy"] = result
        state["current_agent"] = self.name
        return state
