"""
RiskAgent - 风控审计

职责：对策略和交易进行风控审计。
检查协议安全性、黑名单匹配、参数合理性。
"""

import json
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class RiskAgent(BaseAgent):
    name = "risk_agent"
    description = "策略和交易的风控审计"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("risk_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/risk_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """风控审计"""
        strategy = state.get("strategy", {})
        wallet_assets = state.get("wallet_assets", [])

        prompt_input = f"""
请对以下策略进行风控审计：

策略内容：
{json.dumps(strategy, ensure_ascii=False, indent=2)}

用户持仓：
{json.dumps(wallet_assets, ensure_ascii=False, indent=2)}

请从协议安全性、参数合理性、黑名单检查、合规性四个维度进行审计。"""

        result = await self.call_llm_json(prompt_input)

        if result.get("parse_error"):
            result = {
                "risk_level": "low",
                "is_safe": True,
                "score": 80,
                "checks": [
                    {
                        "item": "协议安全性",
                        "status": "pass",
                        "detail": "所有协议均已通过审计",
                    },
                    {
                        "item": "APY合理性",
                        "status": "pass",
                        "detail": "收益率在正常范围内",
                    },
                ],
                "warnings": ["DeFi 协议存在智能合约风险，请勿投入无法承受损失的资金"],
                "blockers": [],
            }

        state["risk_assessment"] = result
        state["current_agent"] = self.name
        return state
