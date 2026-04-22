"""
TDD: MonitoringAgent 测试
验证监控与预警 Agent 的 Mock 实现
"""

import pytest
from agents.monitoring_agent import MonitoringAgent


@pytest.fixture
def data_agg_agent():
    """创建 Mock 模式的 DataAggregationAgent"""
    from agents.data_aggregation_agent import DataAggregationAgent

    return DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)


@pytest.fixture
def agent(data_agg_agent):
    """创建 Mock 模式的 MonitoringAgent"""
    return MonitoringAgent(llm=None, data_aggregation_agent=data_agg_agent, use_mock=True)


@pytest.fixture
def agent_with_strategy_state(agent):
    """创建包含策略和钱包数据的 state"""
    from agents.data_aggregation_agent import DataAggregationAgent
    from mock.chain_data import mock_wallet_data

    data_agg = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
    mon_agent = MonitoringAgent(llm=None, data_aggregation_agent=data_agg, use_mock=True)

    state = {
        "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        "strategy_id": "strat_003",  # critical 状态策略
        "wallet_data": mock_wallet_data,
        "task_type": "strategy_monitor",
    }
    return mon_agent, state


class TestMonitoringAgentInit:
    """MonitoringAgent 初始化测试"""

    def test_mock_mode_no_llm_needed(self):
        """Mock 模式下不需要 LLM"""
        agent = MonitoringAgent(llm=None, data_aggregation_agent=None, use_mock=True)
        assert agent.use_mock is True

    def test_default_is_mock_mode(self):
        """默认应为 Mock 模式"""
        agent = MonitoringAgent(llm=None, data_aggregation_agent=None)
        assert agent.use_mock is True


class TestMonitorStrategy:
    """monitor_strategy 测试"""

    @pytest.mark.asyncio
    async def test_returns_state_with_monitoring_result(self, agent_with_strategy_state):
        """应返回包含 monitoring_result 的 state"""
        agent, state = agent_with_strategy_state
        result = await agent.monitor_strategy(state)
        assert "monitoring_result" in result

    @pytest.mark.asyncio
    async def test_monitoring_result_has_required_fields(self, agent_with_strategy_state):
        """monitoring_result 应包含必需字段"""
        agent, state = agent_with_strategy_state
        result = await agent.monitor_strategy(state)
        mr = result["monitoring_result"]
        required = [
            "strategy_id",
            "status",
            "current_value",
            "initial_value",
            "pnl",
            "pnl_percentage",
            "expected_apy",
            "actual_apy",
            "alerts",
            "suggestions",
            "last_checked",
        ]
        for field in required:
            assert field in mr, f"缺少字段: {field}"

    @pytest.mark.asyncio
    async def test_critical_strategy_has_alerts(self, agent_with_strategy_state):
        """critical 策略应产生预警"""
        agent, state = agent_with_strategy_state
        result = await agent.monitor_strategy(state)
        mr = result["monitoring_result"]
        assert len(mr["alerts"]) > 0
        assert mr["status"] == "critical"

    @pytest.mark.asyncio
    async def test_pnl_calculation_correct(self, agent):
        """PnL 计算应正确"""
        state = {
            "strategy_id": "strat_001",
            "wallet_address": "TestAddr",
        }
        result = await agent.monitor_strategy(state)
        mr = result["monitoring_result"]
        expected_pnl_pct = (mr["current_value"] - mr["initial_value"]) / mr["initial_value"] * 100
        assert abs(mr["pnl_percentage"] - expected_pnl_pct) < 0.01

    @pytest.mark.asyncio
    async def test_stop_loss_detection(self, agent):
        """应检测止损触发条件"""
        state = {
            "strategy_id": "strat_003",
            "wallet_address": "TestAddr",
        }
        result = await agent.monitor_strategy(state)
        mr = result["monitoring_result"]
        alert_types = [a["type"] for a in mr["alerts"]]
        assert "stop_loss" in alert_types

    @pytest.mark.asyncio
    async def test_apy_drift_detection(self, agent):
        """应检测 APY 偏移"""
        state = {
            "strategy_id": "strat_002",
            "wallet_address": "TestAddr",
        }
        result = await agent.monitor_strategy(state)
        mr = result["monitoring_result"]
        alert_types = [a["type"] for a in mr["alerts"]]
        assert "apy_drift" in alert_types


class TestCheckPositionRisk:
    """check_position_risk 测试"""

    @pytest.mark.asyncio
    async def test_detects_low_health_factor(self, agent):
        """应检测低健康因子借贷仓位"""
        from mock.chain_data import generate_mock_wallet

        wallet_data = generate_mock_wallet(include_low_health=True)
        state = {"wallet_data": wallet_data}
        result = await agent.check_position_risk(state)
        assert "risk_alerts" in result
        lending_alerts = [a for a in result["risk_alerts"] if a["type"] == "lending_risk"]
        assert len(lending_alerts) > 0

    @pytest.mark.asyncio
    async def test_critical_severity_for_very_low_health(self, agent):
        """健康因子 < 1.2 应标记为 critical"""
        from mock.chain_data import generate_mock_wallet

        wallet_data = generate_mock_wallet(include_low_health=True)
        state = {"wallet_data": wallet_data}
        result = await agent.check_position_risk(state)
        critical_alerts = [
            a
            for a in result["risk_alerts"]
            if a["type"] == "lending_risk" and a["severity"] == "critical"
        ]
        assert len(critical_alerts) > 0

    @pytest.mark.asyncio
    async def test_no_alerts_for_healthy_positions(self, agent):
        """健康仓位不应产生借贷预警"""
        from mock.chain_data import generate_mock_wallet

        wallet_data = generate_mock_wallet(include_low_health=False)
        state = {"wallet_data": wallet_data}
        result = await agent.check_position_risk(state)
        lending_alerts = [a for a in result["risk_alerts"] if a["type"] == "lending_risk"]
        assert len(lending_alerts) == 0

    @pytest.mark.asyncio
    async def test_detects_high_risk_authorizations(self, agent):
        """应检测高风险授权"""
        from mock.chain_data import mock_wallet_data

        state = {"wallet_data": mock_wallet_data}
        result = await agent.check_position_risk(state)
        auth_alerts = [a for a in result["risk_alerts"] if a["type"] == "authorization_risk"]
        assert len(auth_alerts) > 0


class TestCheckProfitOpportunities:
    """check_profit_opportunities 测试"""

    @pytest.mark.asyncio
    async def test_identifies_better_apy_opportunity(self, agent):
        """应识别更优 APY 机会"""
        state = {
            "wallet_data": {
                "lending_positions": [{"protocol": "Solend", "supply_apy": 2.8}],
            },
            "defi_data": {
                "lending_protocols": {
                    "MarginFi": {"supply_apy": 3.5, "borrow_apy": 5.2, "tvl": 580_000_000},
                    "Solend": {"supply_apy": 2.8, "borrow_apy": 4.5, "tvl": 250_000_000},
                },
            },
        }
        result = await agent.check_profit_opportunities(state)
        assert "opportunities" in result
        assert len(result["opportunities"]) > 0

    @pytest.mark.asyncio
    async def test_opportunity_has_required_fields(self, agent):
        """机会建议应包含必需字段"""
        state = {
            "wallet_data": {
                "lending_positions": [{"protocol": "Solend", "supply_apy": 2.8}],
            },
            "defi_data": {
                "lending_protocols": {
                    "MarginFi": {"supply_apy": 3.5, "borrow_apy": 5.2, "tvl": 580_000_000},
                },
            },
        }
        result = await agent.check_profit_opportunities(state)
        if result["opportunities"]:
            for opp in result["opportunities"]:
                assert "type" in opp
                assert "description" in opp


class TestShouldTriggerAlert:
    """should_trigger_alert 测试"""

    @pytest.mark.asyncio
    async def test_triggers_with_alerts(self, agent):
        """有预警时应触发"""
        monitoring_result = {"alerts": [{"type": "test", "severity": "warning"}]}
        assert await agent.should_trigger_alert(monitoring_result) is True

    @pytest.mark.asyncio
    async def test_no_trigger_without_alerts(self, agent):
        """无预警时不应触发"""
        monitoring_result = {"alerts": []}
        assert await agent.should_trigger_alert(monitoring_result) is False

    @pytest.mark.asyncio
    async def test_triggers_on_pnl_threshold(self, agent):
        """PnL 偏离超阈值应触发"""
        monitoring_result = {
            "alerts": [],
            "pnl_percentage": -15.0,
        }
        assert await agent.should_trigger_alert(monitoring_result) is True

    @pytest.mark.asyncio
    async def test_triggers_on_risk_level_escalation(self, agent):
        """风险等级上升应触发"""
        monitoring_result = {
            "alerts": [],
            "risk_level": "critical",
        }
        assert await agent.should_trigger_alert(monitoring_result) is True


class TestGenerateAlertMessage:
    """generate_alert_message 测试"""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_template_message(self, agent):
        """Mock 模式应返回模板消息"""
        alert = {
            "type": "lending_risk",
            "severity": "critical",
            "message": "借贷健康度过低",
            "suggestion": "补充抵押品",
        }
        message = await agent.generate_alert_message(alert)
        assert isinstance(message, str)
        assert len(message) > 0


class TestCallRouting:
    """__call__ 路由测试"""

    @pytest.mark.asyncio
    async def test_strategy_monitor_task(self, agent):
        """task_type=strategy_monitor 应执行策略监控"""
        state = {
            "wallet_address": "TestAddr",
            "strategy_id": "strat_001",
            "task_type": "strategy_monitor",
        }
        result = await agent(state)
        assert "monitoring_result" in result

    @pytest.mark.asyncio
    async def test_position_check_task(self, agent):
        """task_type=position_check 应执行持仓风险检查"""
        from mock.chain_data import generate_mock_wallet

        state = {
            "wallet_address": "TestAddr",
            "wallet_data": generate_mock_wallet(include_low_health=True),
            "task_type": "position_check",
        }
        result = await agent(state)
        assert "risk_alerts" in result

    @pytest.mark.asyncio
    async def test_opportunity_scan_task(self, agent):
        """task_type=opportunity_scan 应执行收益机会扫描"""
        state = {
            "wallet_address": "TestAddr",
            "task_type": "opportunity_scan",
        }
        result = await agent(state)
        assert "opportunities" in result

    @pytest.mark.asyncio
    async def test_default_runs_all_checks(self, agent):
        """默认 task_type 应运行所有检查"""
        state = {
            "wallet_address": "TestAddr",
            "strategy_id": "strat_001",
        }
        result = await agent(state)
        # 默认应包含 monitoring_result + risk_alerts + opportunities
        assert "monitoring_result" in result or "risk_alerts" in result or "opportunities" in result
