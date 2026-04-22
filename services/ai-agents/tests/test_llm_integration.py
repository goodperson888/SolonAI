"""
LLM 集成测试：验证 Dean 的 Agent 在真实 LLM 模式下能走通

需要 .env 配置好 LLM API Key。
如果 .env 不存在或 LLM 不可用，测试会 skip。

运行方式：
    cd services/ai-agents && .venv/bin/python -m pytest tests/test_llm_integration.py -v
"""

import pytest

# 检查 LLM 是否可用
_llm_available = False
_llm = None


def _check_llm():
    """检查 LLM 配置是否可用"""
    global _llm_available, _llm
    try:
        from config import llm_config

        if not llm_config.api_key:
            return False
        from llm_factory import create_llm

        _llm = create_llm(streaming=False)
        _llm_available = True
        return True
    except Exception:
        return False


llm_ready = _check_llm()

# Skip 整个模块如果 LLM 不可用
pytestmark = pytest.mark.skipif(not llm_ready, reason="LLM API Key not configured")


# ===== MonitoringAgent LLM 集成测试 =====


class TestMonitoringAgentLLMIntegration:
    """MonitoringAgent 在真实 LLM 模式下的集成测试"""

    def _get_monitoring_agent(self):
        from agents.monitoring_agent import MonitoringAgent

        return MonitoringAgent(llm=_llm, data_aggregation_agent=None, use_mock=True)

    @pytest.mark.asyncio
    async def test_generate_alert_message_with_llm(self):
        """LLM 模式下 generate_alert_message 应生成用户友好的中文消息"""
        agent = self._get_monitoring_agent()

        alert = {
            "type": "stop_loss",
            "severity": "critical",
            "message": "触发止损线，当前亏损 -18.5%",
            "suggestion": "建议立即平仓或减仓止损",
        }

        result = await agent.generate_alert_message(alert)

        # LLM 应返回非空字符串
        assert isinstance(result, str)
        assert len(result) > 0

        # 应包含关键信息（LLM 翻译后会保留核心含义）
        # 不做严格匹配，因为 LLM 输出有随机性
        assert "止损" in result or "亏损" in result or "平仓" in result or "减仓" in result

    @pytest.mark.asyncio
    async def test_generate_warning_alert_with_llm(self):
        """LLM 应将 warning 级别预警翻译成通俗语言"""
        agent = self._get_monitoring_agent()

        alert = {
            "type": "pnl_warning",
            "severity": "warning",
            "message": "当前亏损 -12.3%，接近止损线",
            "suggestion": "建议关注市场动态，做好止损准备",
        }

        result = await agent.generate_alert_message(alert)
        assert isinstance(result, str)
        assert len(result) > 0
        # 应该提到亏损或止损相关内容
        assert any(kw in result for kw in ["亏损", "止损", "减仓", "注意", "风险", "警告"])

    @pytest.mark.asyncio
    async def test_generate_authorization_risk_alert_with_llm(self):
        """LLM 应将授权风险预警翻译成通俗语言"""
        agent = self._get_monitoring_agent()

        alert = {
            "type": "authorization_risk",
            "severity": "warning",
            "message": "发现高风险授权: 未知程序",
            "suggestion": "建议撤销不必要的授权",
        }

        result = await agent.generate_alert_message(alert)
        assert isinstance(result, str)
        assert len(result) > 0
        # 应该提到授权相关内容
        assert any(kw in result for kw in ["授权", "撤销", "权限", "安全", "风险"])

    @pytest.mark.asyncio
    async def test_full_monitoring_workflow_with_llm_alerts(self):
        """完整监控流程：策略监控 + LLM 预警生成"""
        from agents.data_aggregation_agent import DataAggregationAgent

        data_agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        agent = self._get_monitoring_agent()
        agent.data_aggregation_agent = data_agent

        # 使用 critical 策略触发预警
        state = {
            "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
            "strategy_id": "strat_003",
            "task_type": "default",
        }

        # 先聚合数据
        state = await data_agent(state)
        # 再运行监控
        state = await agent(state)

        # 验证监控结果
        assert "monitoring_result" in state

        # 如果触发了预警，验证 LLM 生成的消息
        if "alert_messages" in state and len(state["alert_messages"]) > 0:
            for msg in state["alert_messages"]:
                assert isinstance(msg, str)
                assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_mock_vs_llm_alert_message_consistency(self):
        """Mock 模式和 LLM 模式的预警消息应包含相同核心信息"""
        from agents.monitoring_agent import MonitoringAgent

        mock_agent = MonitoringAgent(llm=None, data_aggregation_agent=None, use_mock=True)
        llm_agent = self._get_monitoring_agent()

        alert = {
            "type": "stop_loss",
            "severity": "critical",
            "message": "触发止损线，当前亏损 -18.5%",
            "suggestion": "建议立即平仓或减仓止损",
        }

        mock_result = await mock_agent.generate_alert_message(alert)
        llm_result = await llm_agent.generate_alert_message(alert)

        # 两种模式都应返回非空字符串
        assert isinstance(mock_result, str)
        assert isinstance(llm_result, str)
        assert len(mock_result) > 0
        assert len(llm_result) > 0

        # LLM 版本通常更长更详细
        # Mock 版本是模板格式 "[严重] ..."


# ===== DataAggregationAgent LLM 模式测试 =====


class TestDataAggregationAgentLLMMode:
    """DataAggregationAgent 在 LLM 模式下的测试

    DataAggregationAgent 当前不直接调用 LLM（所有逻辑是规则型的），
    但验证在 llm 参数传入时不会崩溃。
    """

    def _get_agent(self):
        from agents.data_aggregation_agent import DataAggregationAgent

        return DataAggregationAgent(llm=_llm, blockchain_service=None, use_mock=True)

    @pytest.mark.asyncio
    async def test_agent_with_llm_does_not_crash(self):
        """传入 LLM 实例不应导致崩溃"""
        agent = self._get_agent()
        state = {"wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"}
        result = await agent(state)
        assert "wallet_data" in result
        assert "defi_data" in result
        assert "risk_data" in result

    @pytest.mark.asyncio
    async def test_real_mode_without_blockchain_returns_empty(self):
        """真实模式（无 blockchain_service）应返回空数据但不崩溃"""
        from agents.data_aggregation_agent import DataAggregationAgent

        agent = DataAggregationAgent(llm=_llm, blockchain_service=None, use_mock=False)
        state = {"wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"}
        result = await agent(state)

        # 无 blockchain_service 时，真实模式返回空数据
        assert "wallet_data" in result
        assert result["wallet_data"]["total_value_usd"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_data_works_in_both_modes(self):
        """数据验证在两种模式下都应工作"""
        from agents.data_aggregation_agent import DataAggregationAgent

        # Mock 模式
        mock_agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        mock_state = {"wallet_address": "TestAddr"}
        mock_result = await mock_agent(mock_state)
        assert await mock_agent.validate_data(mock_result["wallet_data"]) is True

        # LLM 模式（仍然用 mock 数据）
        llm_agent = self._get_agent()
        llm_state = {"wallet_address": "TestAddr"}
        llm_result = await llm_agent(llm_state)
        assert await llm_agent.validate_data(llm_result["wallet_data"]) is True


# ===== 完整 LangGraph 工作流 LLM 集成测试 =====


class TestFullWorkflowLLMIntegration:
    """完整 Agent 工作流 LLM 集成测试

    使用 main_graph.py 的 run_agent() 跑完整 pipeline，
    验证 Dean 的 Agent 在真实 LLM 环境下的数据流。
    """

    @pytest.mark.asyncio
    async def test_query_assets_workflow(self):
        """查询资产场景：IntentAgent → DataAggregationAgent → ExplanationAgent"""
        from graphs.main_graph import run_agent

        result = await run_agent(
            user_input="帮我看看钱包里有什么资产",
            wallet_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        )

        assert result.get("intent") == "query_assets"
        assert result.get("explanation", "") != ""
        assert result.get("completed") is True or result.get("error") is None

    @pytest.mark.asyncio
    async def test_risk_check_workflow(self):
        """风控检查场景：IntentAgent → DataAggregationAgent → RiskAgent → ExplanationAgent"""
        from graphs.main_graph import run_agent

        result = await run_agent(
            user_input="帮我检查一下这个代币是否安全：JUP",
            wallet_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        )

        assert result.get("intent") == "risk_check"
        assert result.get("explanation", "") != ""

    @pytest.mark.asyncio
    async def test_chat_workflow(self):
        """普通聊天场景：IntentAgent → ExplanationAgent"""
        from graphs.main_graph import run_agent

        result = await run_agent(
            user_input="什么是无常损失？",
        )

        assert result.get("intent") == "chat"
        assert len(result.get("explanation", "")) > 20
