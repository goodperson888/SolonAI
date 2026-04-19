"""
MonitoringAgent - 持续监控

职责：监控用户已执行策略的状态，跟踪收益，检测风险变化。
触发预警条件时生成预警信息和调仓建议。
"""

from datetime import datetime
from typing import Any, Dict

from base_agent import BaseAgent

class MonitoringAgent(BaseAgent):
    name = "monitoring_agent"
    description = "监控策略执行状态，生成预警"

    @property
    def system_prompt(self) -> str:
        return """你是投资监控专家。负责监控用户策略的执行状态。

## 监控维度
1. 收益跟踪：实际收益 vs 预期收益
2. 风险变化：协议TVL变化、APY变化
3. 异常检测：价格剧烈波动、流动性变化
4. 止盈止损：是否达到用户设定的阈值

## 返回 JSON 格式

```json
{
  "status": "normal/warning/critical",
  "current_value": 5100,
  "initial_value": 5000,
  "pnl": 100,
  "pnl_percentage": 2.0,
  "alerts": [
    {
      "type": "apy_change",
      "severity": "low",
      "message": "MarginFi USDC APY从8.2%降至7.5%"
    }
  ],
  "suggestions": ["当前收益正常，建议继续持有"]
}
```"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """监控策略状态"""
        strategy = state.get("strategy", {})
        # transaction = state.get("transaction", {})

        # TODO: 后续对接真实的链上数据
        # 目前返回模拟的监控结果

        total_investment = strategy.get("total_investment", 5000)
        expected_apy = strategy.get("expected_apy", 8.2)

        # 模拟收益计算（假设运行了1天）
        daily_rate = expected_apy / 365 / 100
        current_value = total_investment * (1 + daily_rate)
        pnl = current_value - total_investment

        state["monitoring_config"] = {
            "status": "normal",
            "current_value": round(current_value, 2),
            "initial_value": total_investment,
            "pnl": round(pnl, 2),
            "pnl_percentage": round(pnl / total_investment * 100, 4),
            "expected_apy": expected_apy,
            "alerts": [],
            "suggestions": ["策略运行正常，收益符合预期，建议继续持有"],
            "last_checked": datetime.now().isoformat(),
        }

        state["current_agent"] = self.name
        return state
