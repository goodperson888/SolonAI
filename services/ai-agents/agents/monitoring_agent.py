"""
MonitoringAgent - 持续监控

职责：监控用户已执行策略的状态，跟踪收益，检测风险变化。
触发预警条件时生成预警信息和调仓建议。
"""

from datetime import datetime
from typing import Any, Dict

from base_agent import BaseAgent
from prompts import get_prompt


class MonitoringAgent(BaseAgent):
    name = "monitoring_agent"
    description = "监控策略执行状态，生成预警"

    @property
    def system_prompt(self) -> str:
        """从文件加载 system prompt"""
        return get_prompt("monitoring_agent", language="zh", version="v1")

    # 原 prompt 已移至 prompts/monitoring_agent_zh_v1.txt
    # 如需修改 prompt，请编辑该文件

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
