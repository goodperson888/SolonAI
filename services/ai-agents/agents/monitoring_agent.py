"""
监控与预警Agent
职责：7*24小时监控用户已部署的策略、持仓、授权风险，触发预警条件时自动生成预警信息与处置方案
"""

from typing import Dict, List, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage


class MonitoringAgent:
    """监控与预警Agent - 实时盯盘、异常监控、收益跟踪、预警推送"""

    def __init__(self, llm, data_aggregation_agent):
        self.llm = llm
        self.data_aggregation_agent = data_aggregation_agent
        self.system_prompt = """你是Solon AI的监控与预警专家。
你的职责是：
1. 7*24小时监控用户的策略执行情况
2. 实时跟踪持仓收益和风险变化
3. 识别异常情况并生成预警
4. 提供调仓建议和处置方案

核心能力：
- 实时盯盘
- 异常监控
- 收益跟踪
- 预警推送
- 调仓建议生成
"""

    async def monitor_strategy(self, state: Dict) -> Dict:
        """
        监控策略执行情况

        Args:
            state: 包含strategy_id的全局状态

        Returns:
            更新后的state，包含monitoring_result字段
        """
        strategy_id = state.get("strategy_id")

        # TODO: AI团队实现以下功能
        # 1. 获取策略当前状态
        # 2. 计算实际收益 vs 预期收益
        # 3. 检查是否触发止盈/止损条件
        # 4. 检查协议APY变化
        # 5. 检查持仓风险变化

        monitoring_result = {
            "strategy_id": strategy_id,
            "status": "active",  # active, warning, critical
            "current_value": 0.0,
            "initial_value": 0.0,
            "pnl": 0.0,
            "pnl_percentage": 0.0,
            "expected_apy": 0.0,
            "actual_apy": 0.0,
            "alerts": [],  # 预警列表
            "suggestions": [],  # 调仓建议
            "last_checked": datetime.now().isoformat()
        }

        state["monitoring_result"] = monitoring_result
        return state

    async def check_position_risk(self, state: Dict) -> Dict:
        """
        检查持仓风险

        Args:
            state: 包含wallet_data的全局状态

        Returns:
            更新后的state，包含risk_alerts字段
        """
        wallet_data = state.get("wallet_data", {})

        # TODO: AI团队实现以下功能
        # 1. 检查借贷健康度
        # 2. 检查LP无常损失
        # 3. 检查代币价格异常波动
        # 4. 检查授权风险
        # 5. 生成风险预警

        risk_alerts = []

        # 示例：检查借贷健康度
        for position in wallet_data.get("lending_positions", []):
            health_factor = position.get("health", 1.0)
            if health_factor < 1.2:
                risk_alerts.append({
                    "type": "lending_risk",
                    "severity": "critical",
                    "message": f"借贷健康度过低 ({health_factor:.2f})，有清算风险",
                    "suggestion": "建议立即补充抵押品或偿还部分借款",
                    "protocol": position.get("protocol")
                })

        state["risk_alerts"] = risk_alerts
        return state

    async def check_profit_opportunities(self, state: Dict) -> Dict:
        """
        检查收益优化机会

        Args:
            state: 全局状态

        Returns:
            更新后的state，包含opportunities字段
        """
        # TODO: AI团队实现以下功能
        # 1. 对比当前策略 vs 市场最优APY
        # 2. 识别套利机会
        # 3. 发现新的高收益协议
        # 4. 生成收益优化建议

        opportunities = []

        state["opportunities"] = opportunities
        return state

    async def generate_alert_message(self, alert: Dict) -> str:
        """
        生成预警消息（大白话）

        Args:
            alert: 预警信息

        Returns:
            用户友好的预警消息
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
请将以下预警信息翻译成大白话，让普通用户能看懂：

预警类型: {alert.get('type')}
严重程度: {alert.get('severity')}
详细信息: {alert.get('message')}
建议操作: {alert.get('suggestion')}

要求：
1. 用简单易懂的语言
2. 明确告知风险和后果
3. 提供具体的操作建议
4. 语气友好但严肃
""")
        ]

        # TODO: AI团队调用大模型生成用户友好的消息
        response = await self.llm.ainvoke(messages)
        return response.content

    async def should_trigger_alert(self, monitoring_result: Dict) -> bool:
        """
        判断是否应该触发预警

        Args:
            monitoring_result: 监控结果

        Returns:
            是否触发预警
        """
        # TODO: AI团队实现预警触发逻辑
        # 1. 收益偏离预期超过阈值
        # 2. 风险等级上升
        # 3. 协议出现异常
        # 4. 达到止盈/止损条件

        alerts = monitoring_result.get("alerts", [])
        return len(alerts) > 0

    async def __call__(self, state: Dict) -> Dict:
        """
        Agent主入口
        """
        # 1. 监控策略
        if state.get("strategy_id"):
            state = await self.monitor_strategy(state)

        # 2. 检查持仓风险
        if state.get("wallet_data"):
            state = await self.check_position_risk(state)

        # 3. 检查收益机会
        state = await self.check_profit_opportunities(state)

        # 4. 生成预警消息
        monitoring_result = state.get("monitoring_result", {})
        if await self.should_trigger_alert(monitoring_result):
            alerts = monitoring_result.get("alerts", [])
            alert_messages = []
            for alert in alerts:
                message = await self.generate_alert_message(alert)
                alert_messages.append(message)
            state["alert_messages"] = alert_messages

        return state
