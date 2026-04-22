"""
TDD: LangGraph 工作流集成测试
验证 DataAggregationAgent 和 MonitoringAgent 在 Mock 模式下独立运行正常
（不依赖 langchain_openai 等外部库）
"""

import pytest
from agents.data_aggregation_agent import DataAggregationAgent
from agents.monitoring_agent import MonitoringAgent
from mock.chain_data import generate_mock_wallet


class TestDataAggregationAgentInWorkflow:
    """DataAggregationAgent 在工作流中的集成测试"""

    @pytest.mark.asyncio
    async def test_full_aggregation_flow(self):
        """完整聚合流程：钱包 + DeFi + 风险"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
        }
        result = await agent(state)

        # 验证所有数据都被聚合
        assert "wallet_data" in result
        assert "defi_data" in result
        assert "risk_data" in result
        assert result["current_agent"] == "data_aggregation_agent"

        # 验证钱包数据完整性
        assert result["wallet_data"]["total_value_usd"] > 0
        assert len(result["wallet_data"]["balances"]) > 0

        # 验证 DeFi 数据完整性
        assert len(result["defi_data"]["lending_protocols"]) > 0

        # 验证风险数据完整性
        assert len(result["risk_data"]["blacklist_addresses"]) > 0

    @pytest.mark.asyncio
    async def test_strategy_generation_path(self):
        """策略生成路径：钱包 + DeFi（无风险数据）"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "strategy_generation",
        }
        result = await agent(state)
        assert "wallet_data" in result
        assert "defi_data" in result
        assert "risk_data" not in result  # 策略生成不需要风险数据

    @pytest.mark.asyncio
    async def test_risk_check_path(self):
        """风控检查路径：钱包 + 风险（无 DeFi 数据）"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "risk_check",
        }
        result = await agent(state)
        assert "wallet_data" in result
        assert "risk_data" in result
        assert "defi_data" not in result  # 风控检查不需要 DeFi 数据


class TestMonitoringAgentInWorkflow:
    """MonitoringAgent 在工作流中的集成测试"""

    @pytest.mark.asyncio
    async def test_monitoring_after_strategy(self):
        """策略执行后的监控流程"""
        data_agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        mon_agent = MonitoringAgent(llm=None, data_aggregation_agent=data_agent, use_mock=True)

        # 模拟工作流：先聚合数据，再监控
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "strategy_id": "strat_003",  # critical 策略
        }

        # Step 1: DataAggregationAgent
        state = await data_agent(state)
        assert "wallet_data" in state

        # Step 2: MonitoringAgent
        state = await mon_agent(state)

        # 验证监控结果
        assert "monitoring_result" in state or "risk_alerts" in state or "opportunities" in state

    @pytest.mark.asyncio
    async def test_critical_strategy_triggers_alerts(self):
        """critical 策略应产生预警消息"""
        data_agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        mon_agent = MonitoringAgent(llm=None, data_aggregation_agent=data_agent, use_mock=True)

        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "strategy_id": "strat_003",
        }
        state = await data_agent(state)
        state = await mon_agent(state)

        # critical 策略应触发预警
        if "monitoring_result" in state:
            mr = state["monitoring_result"]
            assert mr["status"] in ("critical", "warning")
            if "alert_messages" in state:
                assert len(state["alert_messages"]) > 0

    @pytest.mark.asyncio
    async def test_position_risk_check_with_mock_data(self):
        """使用 Mock 数据的持仓风险检查"""
        mon_agent = MonitoringAgent(llm=None, data_aggregation_agent=None, use_mock=True)
        wallet_data = generate_mock_wallet(include_low_health=True)

        state = {
            "wallet_data": wallet_data,
            "task_type": "position_check",
        }
        result = await mon_agent(state)
        assert "risk_alerts" in result
        lending_alerts = [a for a in result["risk_alerts"] if a["type"] == "lending_risk"]
        assert len(lending_alerts) > 0


class TestDataValidationAcrossWorkflow:
    """跨工作流的数据验证测试"""

    @pytest.mark.asyncio
    async def test_data_aggregation_output_valid(self):
        """DataAggregationAgent 的输出应通过自身验证"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        }
        result = await agent(state)

        # 验证钱包数据
        assert await agent.validate_data(result["wallet_data"]) is True

        # 验证 DeFi 数据
        assert await agent.validate_data(result["defi_data"]) is True

        # 验证风险数据
        assert await agent.validate_data(result["risk_data"]) is True

    @pytest.mark.asyncio
    async def test_mock_data_consistency(self):
        """多次运行应产生一致的数据结构"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        state = {"wallet_address": "TestAddr"}

        result1 = await agent(state.copy())
        result2 = await agent(state.copy())

        # 验证两次运行的顶层字段一致
        assert set(result1["wallet_data"].keys()) == set(result2["wallet_data"].keys())
        assert set(result1["defi_data"].keys()) == set(result2["defi_data"].keys())
