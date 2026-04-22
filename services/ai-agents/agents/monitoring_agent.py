"""
MonitoringAgent - 持续监控

职责：监控用户已执行策略的状态，跟踪收益，检测风险变化。
触发预警条件时生成预警信息和调仓建议。
支持 Mock 模式用于开发和测试。
"""

from datetime import datetime
from typing import Dict, List

from mock.chain_data import mock_strategy_data

# 预警触发阈值
PNL_WARNING_THRESHOLD = -10.0  # PnL 低于 -10% 触发预警
STOP_LOSS_THRESHOLD = -15.0    # PnL 低于 -15% 触发止损
APY_DRIFT_THRESHOLD = 0.5      # APY 偏移超过 50% 触发预警


class MonitoringAgent:
    """监控与预警Agent - 实时盯盘、异常监控、收益跟踪、预警推送"""

    name = "monitoring_agent"
    description = "监控策略执行状态，生成预警"

    def __init__(self, llm=None, data_aggregation_agent=None, use_mock: bool = True):
        self.llm = llm
        self.data_aggregation_agent = data_aggregation_agent
        self.use_mock = use_mock
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

        # 从 Mock 数据中查找策略
        strategy_data = None
        if self.use_mock and strategy_id:
            for s in mock_strategy_data:
                if s["strategy_id"] == strategy_id:
                    strategy_data = s
                    break
            # 如果没找到指定策略，使用第一个
            if strategy_data is None and mock_strategy_data:
                strategy_data = mock_strategy_data[0]

        if strategy_data is None:
            # 默认空监控结果
            strategy_data = {
                "strategy_id": strategy_id or "unknown",
                "status": "active",
                "current_value": 0.0,
                "initial_value": 0.0,
                "pnl": 0.0,
                "pnl_percentage": 0.0,
                "expected_apy": 0.0,
                "actual_apy": 0.0,
                "alerts": [],
                "suggestions": [],
            }

        # 添加预警检测
        alerts = list(strategy_data.get("alerts", []))
        suggestions = list(strategy_data.get("suggestions", []))

        pnl_pct = strategy_data.get("pnl_percentage", 0)
        expected_apy = strategy_data.get("expected_apy", 0)
        actual_apy = strategy_data.get("actual_apy", 0)

        # 止损检测
        if pnl_pct <= STOP_LOSS_THRESHOLD:
            if not any(a.get("type") == "stop_loss" for a in alerts):
                alerts.append({
                    "type": "stop_loss",
                    "severity": "critical",
                    "message": f"触发止损线，当前亏损 {pnl_pct:.1f}%",
                })
                suggestions.append("建议立即平仓或减仓止损")

        # APY 偏移检测
        if expected_apy > 0 and actual_apy >= 0:
            apy_drift = abs(actual_apy - expected_apy) / expected_apy
            if apy_drift > APY_DRIFT_THRESHOLD:
                if not any(a.get("type") == "apy_drift" for a in alerts):
                    alerts.append({
                        "type": "apy_drift",
                        "severity": "warning",
                        "message": f"实际 APY ({actual_apy:.1f}%) 严重偏离预期 ({expected_apy:.1f}%)",
                    })

        # PnL 预警检测
        if pnl_pct <= PNL_WARNING_THRESHOLD and pnl_pct > STOP_LOSS_THRESHOLD:
            if not any(a.get("type") == "pnl_warning" for a in alerts):
                alerts.append({
                    "type": "pnl_warning",
                    "severity": "warning",
                    "message": f"当前亏损 {pnl_pct:.1f}%，接近止损线",
                })

        # 确定整体状态
        if any(a.get("severity") == "critical" for a in alerts):
            status = "critical"
        elif any(a.get("severity") == "warning" for a in alerts):
            status = "warning"
        else:
            status = "active"

        monitoring_result = {
            "strategy_id": strategy_id or "unknown",
            "status": status,
            "current_value": strategy_data.get("current_value", 0.0),
            "initial_value": strategy_data.get("initial_value", 0.0),
            "pnl": strategy_data.get("pnl", 0.0),
            "pnl_percentage": pnl_pct,
            "expected_apy": expected_apy,
            "actual_apy": actual_apy,
            "alerts": alerts,
            "suggestions": suggestions,
            "last_checked": datetime.now().isoformat(),
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
        risk_alerts: List[Dict] = []

        # 检查借贷健康度
        for position in wallet_data.get("lending_positions", []):
            health_factor = position.get("health", 1.0)
            if health_factor < 1.2:
                risk_alerts.append({
                    "type": "lending_risk",
                    "severity": "critical",
                    "message": f"借贷健康度过低 ({health_factor:.2f})，有清算风险",
                    "suggestion": "建议立即补充抵押品或偿还部分借款",
                    "protocol": position.get("protocol"),
                })

        # 检查授权风险
        for auth in wallet_data.get("authorizations", []):
            if auth.get("risk_level") == "high":
                risk_alerts.append({
                    "type": "authorization_risk",
                    "severity": "warning",
                    "message": f"发现高风险授权: {auth.get('program', '未知程序')}",
                    "suggestion": "建议撤销不必要的授权",
                    "protocol": auth.get("program"),
                })

        # 检查 LP 无常损失（简化版：标记所有 LP 仓位供监控）
        for _lp in wallet_data.get("lp_positions", []):
            # TODO: 后续对接真实价格数据计算实际无常损失
            pass

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
        opportunities: List[Dict] = []
        wallet_data = state.get("wallet_data", {})
        defi_data = state.get("defi_data", {})

        # 如果没有 DeFi 数据，先聚合
        if not defi_data and self.data_aggregation_agent:
            state = await self.data_aggregation_agent.aggregate_defi_data(state)
            defi_data = state.get("defi_data", {})

        # 对比当前借贷仓位 APY vs 市场最优
        lending_protocols = defi_data.get("lending_protocols", {})
        current_positions = wallet_data.get("lending_positions", [])

        if lending_protocols and current_positions:
            # 找到最高 supply_apy 的协议
            best_protocol = max(
                lending_protocols.items(),
                key=lambda x: x[1].get("supply_apy", 0),
            )
            best_name, best_info = best_protocol
            best_apy = best_info.get("supply_apy", 0)

            for position in current_positions:
                current_protocol = position.get("protocol", "")
                current_apy = position.get("supply_apy", 0)

                # 如果没有 supply_apy 字段，从 defi_data 查找
                if not current_apy and current_protocol in lending_protocols:
                    current_apy = lending_protocols[current_protocol].get("supply_apy", 0)

                # 如果当前 APY 低于最优 APY 超过 0.5%，建议调仓
                if current_apy > 0 and best_apy > current_apy + 0.5:
                    opportunities.append({
                        "type": "better_apy",
                        "description": f"{current_protocol} APY {current_apy:.1f}% -> {best_name} APY {best_apy:.1f}%",
                        "from_protocol": current_protocol,
                        "to_protocol": best_name,
                        "apy_improvement": best_apy - current_apy,
                    })

        # 如果没有钱包数据但有 DeFi 数据，生成通用建议
        if not current_positions and lending_protocols:
            best_protocol = max(
                lending_protocols.items(),
                key=lambda x: x[1].get("supply_apy", 0),
            )
            best_name, best_info = best_protocol
            opportunities.append({
                "type": "new_deposit",
                "description": f"推荐存入 {best_name}，APY {best_info.get('supply_apy', 0):.1f}%",
                "to_protocol": best_name,
            })

        state["opportunities"] = opportunities
        return state

    async def generate_alert_message(self, alert: Dict) -> str:
        """
        生成预警消息

        Args:
            alert: 预警信息

        Returns:
            用户友好的预警消息
        """
        if self.use_mock:
            # Mock 模式：返回模板消息
            severity_map = {
                "critical": "严重",
                "warning": "警告",
                "low": "提示",
            }
            severity_text = severity_map.get(alert.get("severity", ""), "提示")
            return (
                f"[{severity_text}] {alert.get('message', '未知预警')}\n"
                f"建议操作: {alert.get('suggestion', '请关注')}"
            )

        # 真实模式：调用 LLM 生成用户友好的消息
        if self.llm:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(
                    content=f"""
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
"""
                ),
            ]
            response = await self.llm.ainvoke(messages)
            return response.content

        # 兜底：返回原始消息
        return alert.get("message", "未知预警")

    async def should_trigger_alert(self, monitoring_result: Dict) -> bool:
        """
        判断是否应该触发预警

        Args:
            monitoring_result: 监控结果

        Returns:
            是否触发预警
        """
        alerts = monitoring_result.get("alerts", [])
        if alerts:
            return True

        # PnL 偏离超阈值
        pnl_pct = monitoring_result.get("pnl_percentage", 0)
        if pnl_pct <= PNL_WARNING_THRESHOLD:
            return True

        # 风险等级上升
        risk_level = monitoring_result.get("risk_level", "")
        if risk_level in ("critical", "high"):
            return True

        return False

    async def __call__(self, state: Dict) -> Dict:
        """
        Agent主入口
        """
        task_type = state.get("task_type")

        if task_type == "strategy_monitor":
            if state.get("strategy_id"):
                state = await self.monitor_strategy(state)

        elif task_type == "position_check":
            if state.get("wallet_data"):
                state = await self.check_position_risk(state)

        elif task_type == "opportunity_scan":
            state = await self.check_profit_opportunities(state)

        else:
            # 默认运行所有检查
            if state.get("strategy_id"):
                state = await self.monitor_strategy(state)
            if state.get("wallet_data"):
                state = await self.check_position_risk(state)
            state = await self.check_profit_opportunities(state)

        # 生成预警消息
        monitoring_result = state.get("monitoring_result", {})
        if await self.should_trigger_alert(monitoring_result):
            alerts = monitoring_result.get("alerts", [])
            alert_messages = []
            for alert in alerts:
                message = await self.generate_alert_message(alert)
                alert_messages.append(message)
            state["alert_messages"] = alert_messages

        state["current_agent"] = self.name
        return state
