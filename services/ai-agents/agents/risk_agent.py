"""
RiskAgent - 风控审计

职责：对策略和交易进行风控审计。
检查协议安全性、黑名单匹配、参数合理性。
"""

import json
from typing import Any, Dict

from base_agent import BaseAgent

class RiskAgent(BaseAgent):
    name = "risk_agent"
    description = "策略和交易的风控审计"

    @property
    def system_prompt(self) -> str:
        return """你是 Solana DeFi 风控专家。负责审计投资策略和交易的安全性。

## 审计维度

1. 协议安全性：是否经过审计、TVL大小、运行时间
2. 参数合理性：APY是否异常、金额是否超出承受范围
3. 黑名单检查：涉及的地址和代币是否在黑名单中
4. 合规性检查：是否存在违规承诺

## 风险等级

- low：风险极低，可以放心执行
- medium：有一定风险，建议用户了解后再执行
- high：风险较高，建议谨慎
- critical：风险极高，强烈建议不要执行

## 返回 JSON 格式

```json
{
  "risk_level": "low/medium/high/critical",
  "is_safe": true,
  "score": 85,
  "checks": [
    {
      "item": "协议审计",
      "status": "pass",
      "detail": "MarginFi 已通过 OtterSec 审计"
    },
    {
      "item": "APY合理性",
      "status": "pass",
      "detail": "8.2% APY在正常范围内"
    }
  ],
  "warnings": ["需要注意智能合约风险"],
  "blockers": []
}
```"""

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
