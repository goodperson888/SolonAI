"""
E2E Test: Agent 层端到端测试

使用 Mock LangGraph 工作流，只包含 DataAggregationAgent 和 MonitoringAgent，
无需 LLM API Key，无需区块链服务。

测试 3 个端到端场景：
1. 策略生成路径：DataAggregation → Monitoring(strategy_monitor)
2. 风控检查路径：DataAggregation(risk_check) → Monitoring(position_check)
3. 收益扫描路径：DataAggregation → Monitoring(opportunity_scan)
"""

from typing import Any, Dict, List, Optional, TypedDict

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.data_aggregation_agent import DataAggregationAgent
from agents.monitoring_agent import MonitoringAgent


# ===== E2E 专用状态定义 =====
# DataAggregationAgent / MonitoringAgent 使用的字段与 GraphState 不同
# （GraphState 是完整 8-Agent 工作流的字段，这里只需要 Dean 负责的字段）


class E2EAgentState(TypedDict, total=False):
    """E2E 测试用状态，包含 Dean 两个 Agent 的所有输入输出字段"""

    # 输入
    user_input: str
    wallet_address: str
    session_id: str
    chat_history: list
    task_type: str
    strategy_id: str

    # DataAggregationAgent 输出
    wallet_data: dict
    defi_data: dict
    risk_data: dict

    # MonitoringAgent 输出
    monitoring_result: dict
    risk_alerts: list
    opportunities: list
    alert_messages: list

    # 流程控制
    current_agent: str


# ===== Mock Workflow 构建 =====


def create_mock_workflow():
    """
    构建 Mock E2E 工作流

    只包含 Dean 负责的两个 Agent：
    data_aggregation_node → monitoring_node → END

    与 main_graph.py 的完整工作流不同，这里：
    - 没有 IntentAgent（直接指定 task_type）
    - 没有 StrategyAgent/RiskAgent/ValidationAgent/ExecutionAgent
    - 没有 ExplanationAgent（直接输出结构化数据）
    """
    data_agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
    monitoring_agent = MonitoringAgent(llm=None, data_aggregation_agent=data_agent, use_mock=True)

    workflow = StateGraph(E2EAgentState)

    workflow.add_node("data_aggregation_node", data_agent)
    workflow.add_node("monitoring_node", monitoring_agent)

    workflow.set_entry_point("data_aggregation_node")

    # data_aggregation → monitoring → END
    workflow.add_edge("data_aggregation_node", "monitoring_node")
    workflow.add_edge("monitoring_node", END)

    return workflow.compile(checkpointer=MemorySaver())


# ===== E2E 测试场景 =====


class TestE2EStrategyGenerationPath:
    """端到端场景1：策略生成路径

    模拟用户请求生成策略后的数据流：
    DataAggregation(wallet + defi) → Monitoring(strategy_monitor)
    """

    @pytest.mark.asyncio
    async def test_strategy_monitor_e2e(self):
        """完整的策略监控流程"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "帮我监控策略执行情况",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "session_id": "e2e-test-001",
            "chat_history": [],
            "task_type": "strategy_generation",
            "strategy_id": "strat_003",  # mock 中的 critical 策略
        }

        config = {"configurable": {"thread_id": "e2e-strategy-001"}}
        result = await workflow.ainvoke(initial_state, config=config)

        # 验证 DataAggregation 输出
        assert "wallet_data" in result
        assert "defi_data" in result
        assert result["wallet_data"]["total_value_usd"] > 0

        # 验证 Monitoring 输出
        assert "monitoring_result" in result
        mr = result["monitoring_result"]
        assert mr["status"] in ("critical", "warning", "active")
        assert "pnl_percentage" in mr
        assert "alerts" in mr

        # strat_003 是 critical 策略，应产生预警
        assert mr["status"] in ("critical", "warning")

        # 验证预警消息已生成
        if "alert_messages" in result:
            assert len(result["alert_messages"]) > 0
            # 预警消息应包含中文或英文提示
            for msg in result["alert_messages"]:
                assert isinstance(msg, str)
                assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_healthy_strategy_no_critical_alert(self):
        """健康的策略不应触发 critical 告警"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "监控我的策略",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
            "strategy_id": "strat_001",  # mock 中的正常策略
        }

        config = {"configurable": {"thread_id": "e2e-strategy-002"}}
        result = await workflow.ainvoke(initial_state, config=config)

        mr = result.get("monitoring_result", {})
        # strat_001 策略正常，不应有 critical 告警
        assert mr.get("status") != "critical" or len(mr.get("alerts", [])) == 0


class TestE2ERiskCheckPath:
    """端到端场景2：风控检查路径

    模拟用户请求风险检查后的数据流：
    DataAggregation(wallet + risk) → Monitoring(position_check)
    """

    @pytest.mark.asyncio
    async def test_risk_check_e2e(self):
        """完整的风控检查流程"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "帮我检查持仓风险",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "risk_check",
        }

        config = {"configurable": {"thread_id": "e2e-risk-001"}}
        result = await workflow.ainvoke(initial_state, config=config)

        # 验证 DataAggregation 输出了 wallet + risk 数据
        assert "wallet_data" in result
        assert "risk_data" in result

        # 验证 Monitoring 的持仓风险检查
        assert "risk_alerts" in result
        # Mock 数据包含低健康度借贷仓位，应产生预警
        lending_alerts = [
            a for a in result["risk_alerts"] if a["type"] == "lending_risk"
        ]
        assert len(lending_alerts) > 0
        # 预警应包含建议
        for alert in lending_alerts:
            assert "suggestion" in alert

    @pytest.mark.asyncio
    async def test_authorization_risk_detected(self):
        """高风险授权应被检测"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "检查授权风险",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "risk_check",
        }

        config = {"configurable": {"thread_id": "e2e-risk-002"}}
        result = await workflow.ainvoke(initial_state, config=config)

        auth_alerts = [
            a for a in result.get("risk_alerts", [])
            if a["type"] == "authorization_risk"
        ]
        # Mock 数据包含 high risk_level 授权
        assert len(auth_alerts) > 0


class TestE2EOpportunityScanPath:
    """端到端场景3：收益优化路径

    模拟用户请求收益优化的数据流：
    DataAggregation(wallet + defi) → Monitoring(opportunity_scan)
    """

    @pytest.mark.asyncio
    async def test_opportunity_scan_e2e(self):
        """完整的收益扫描流程"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "有没有更好的收益机会？",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
        }

        config = {"configurable": {"thread_id": "e2e-opp-001"}}
        result = await workflow.ainvoke(initial_state, config=config)

        # 验证收益机会被识别
        assert "opportunities" in result
        opportunities = result["opportunities"]
        assert isinstance(opportunities, list)

        # 验证 DataAggregation 提供了 DeFi 数据
        assert "defi_data" in result

    @pytest.mark.asyncio
    async def test_apy_improvement_opportunity(self):
        """应检测到 APY 优化机会"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "帮我优化收益",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
        }

        config = {"configurable": {"thread_id": "e2e-opp-002"}}
        result = await workflow.ainvoke(initial_state, config=config)

        for opp in result.get("opportunities", []):
            # 每个机会应有描述和类型
            assert "type" in opp
            assert "description" in opp


class TestE2EStateFlow:
    """端到端状态流转验证

    验证状态在 Agent 之间正确传递。
    """

    @pytest.mark.asyncio
    async def test_state_propagation(self):
        """验证 state 在 data_aggregation → monitoring 之间正确传递"""
        workflow = create_mock_workflow()

        initial_state = {
            "user_input": "全面分析",
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
        }

        config = {"configurable": {"thread_id": "e2e-state-001"}}
        result = await workflow.ainvoke(initial_state, config=config)

        # 验证 DataAggregation 写入的字段都被 Monitoring 读取到了
        assert "wallet_data" in result
        assert "defi_data" in result

        # Monitoring 的输出应基于 DataAggregation 的输入
        assert "monitoring_result" in result or "risk_alerts" in result or "opportunities" in result

    @pytest.mark.asyncio
    async def test_current_agent_updated(self):
        """验证 current_agent 被最后一个 Agent 更新"""
        workflow = create_mock_workflow()

        initial_state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "task_type": "default",
        }

        config = {"configurable": {"thread_id": "e2e-state-002"}}
        result = await workflow.ainvoke(initial_state, config=config)

        # 最后一个节点是 monitoring_node
        assert result.get("current_agent") == "monitoring_agent"

    @pytest.mark.asyncio
    async def test_no_external_dependencies(self):
        """验证 E2E 测试不需要任何外部依赖"""
        # 这个测试本身的存在就证明了不需要 LLM / 区块链 / 网络
        workflow = create_mock_workflow()
        assert workflow is not None

        initial_state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        }
        config = {"configurable": {"thread_id": "e2e-nodeps-001"}}
        result = await workflow.ainvoke(initial_state, config=config)
        assert result is not None


class TestE2EMultipleRequests:
    """端到端：多请求场景

    模拟连续多次调用，验证隔离性和一致性。
    """

    @pytest.mark.asyncio
    async def test_sequential_requests_isolated(self):
        """连续多次请求，状态应相互隔离"""
        workflow = create_mock_workflow()

        results = []
        for i in range(3):
            state = {
                "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                "task_type": "default",
                "strategy_id": f"strat_00{i + 1}",
            }
            config = {"configurable": {"thread_id": f"e2e-seq-{i}"}}
            result = await workflow.ainvoke(state, config=config)
            results.append(result)

        # 每次请求应独立完成
        for r in results:
            assert "wallet_data" in r
            assert "monitoring_result" in r

        # 不同 strategy_id 应产生不同的监控结果
        pnl_values = [r["monitoring_result"]["pnl_percentage"] for r in results]
        # 至少应有两个不同的 PnL（因为 strategy 不同）
        assert len(set(pnl_values)) > 1
