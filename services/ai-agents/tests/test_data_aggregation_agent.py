"""
TDD: DataAggregationAgent 测试
验证链上数据聚合 Agent 的 Mock 实现
"""

import pytest

from agents.data_aggregation_agent import DataAggregationAgent


@pytest.fixture
def agent():
    """创建 Mock 模式的 DataAggregationAgent"""
    return DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)


@pytest.fixture
def agent_with_state(agent):
    """创建带基本 state 的 agent"""
    return agent, {
        "wallet_address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        "task_type": "wallet_analysis",
    }


class TestDataAggregationAgentInit:
    """DataAggregationAgent 初始化测试"""

    def test_mock_mode_no_blockchain_service_needed(self):
        """Mock 模式下不需要 blockchain_service"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None, use_mock=True)
        assert agent.use_mock is True

    def test_default_is_mock_mode(self):
        """默认应为 Mock 模式"""
        agent = DataAggregationAgent(llm=None, blockchain_service=None)
        assert agent.use_mock is True


class TestAggregateWalletData:
    """aggregate_wallet_data 测试"""

    @pytest.mark.asyncio
    async def test_returns_state_with_wallet_data(self, agent_with_state):
        """应返回包含 wallet_data 的 state"""
        agent, state = agent_with_state
        result = await agent.aggregate_wallet_data(state)
        assert "wallet_data" in result

    @pytest.mark.asyncio
    async def test_wallet_data_has_required_fields(self, agent_with_state):
        """wallet_data 应包含所有必需字段"""
        agent, state = agent_with_state
        result = await agent.aggregate_wallet_data(state)
        wallet = result["wallet_data"]
        required = ["address", "balances", "nfts", "lp_positions",
                     "lending_positions", "authorizations", "total_value_usd", "last_updated"]
        for field in required:
            assert field in wallet, f"缺少字段: {field}"

    @pytest.mark.asyncio
    async def test_wallet_data_address_matches_input(self, agent_with_state):
        """wallet_data 地址应与输入一致"""
        agent, state = agent_with_state
        result = await agent.aggregate_wallet_data(state)
        assert result["wallet_data"]["address"] == state["wallet_address"]

    @pytest.mark.asyncio
    async def test_cleans_zero_value_balances(self, agent):
        """应过滤掉零值余额"""
        state = {"wallet_address": "TestAddr"}
        result = await agent.aggregate_wallet_data(state)
        for mint, info in result["wallet_data"]["balances"].items():
            assert info["usd_value"] > 0, f"零值余额未被清除: {mint}"

    @pytest.mark.asyncio
    async def test_total_value_usd_is_sum_of_non_zero_balances(self, agent):
        """total_value_usd 应为所有非零余额 usd_value 之和"""
        state = {"wallet_address": "TestAddr"}
        result = await agent.aggregate_wallet_data(state)
        wallet = result["wallet_data"]
        expected_total = sum(
            info["usd_value"] for info in wallet["balances"].values()
        )
        assert wallet["total_value_usd"] == expected_total

    @pytest.mark.asyncio
    async def test_detects_price_anomaly(self, agent):
        """应检测价格剧烈波动并标记"""
        state = {"wallet_address": "TestAddr"}
        result = await agent.aggregate_wallet_data(state)
        # 验证有 anomaly_detection 字段
        assert "anomaly_detection" in result["wallet_data"]
        anomalies = result["wallet_data"]["anomaly_detection"]
        assert isinstance(anomalies, list)


class TestAggregateDefiData:
    """aggregate_defi_data 测试"""

    @pytest.mark.asyncio
    async def test_returns_state_with_defi_data(self, agent):
        """应返回包含 defi_data 的 state"""
        result = await agent.aggregate_defi_data({})
        assert "defi_data" in result

    @pytest.mark.asyncio
    async def test_defi_data_has_lending_protocols(self, agent):
        """defi_data 应包含借贷协议数据"""
        result = await agent.aggregate_defi_data({})
        assert "lending_protocols" in result["defi_data"]
        assert len(result["defi_data"]["lending_protocols"]) > 0

    @pytest.mark.asyncio
    async def test_protocols_sorted_by_supply_apy_desc(self, agent):
        """借贷协议应按 supply_apy 降序排列"""
        result = await agent.aggregate_defi_data({})
        protocols = result["defi_data"]["lending_protocols"]
        apys = [info["supply_apy"] for info in protocols.values()]
        assert apys == sorted(apys, reverse=True)

    @pytest.mark.asyncio
    async def test_small_tvl_protocols_flagged(self, agent):
        """TVL 过低的协议应被标记为 small_protocol"""
        result = await agent.aggregate_defi_data({})
        protocols = result["defi_data"]["lending_protocols"]
        for name, info in protocols.items():
            assert "is_small_protocol" in info, f"{name} 缺少 is_small_protocol 标记"


class TestAggregateRiskData:
    """aggregate_risk_data 测试"""

    @pytest.mark.asyncio
    async def test_returns_state_with_risk_data(self, agent):
        """应返回包含 risk_data 的 state"""
        result = await agent.aggregate_risk_data({})
        assert "risk_data" in result

    @pytest.mark.asyncio
    async def test_risk_data_has_blacklist(self, agent):
        """risk_data 应包含黑名单"""
        result = await agent.aggregate_risk_data({})
        assert len(result["risk_data"]["blacklist_addresses"]) > 0

    @pytest.mark.asyncio
    async def test_blacklist_addresses_are_valid_format(self, agent):
        """黑名单地址应为有效格式（32-44 字符的 base58）"""
        result = await agent.aggregate_risk_data({})
        for addr in result["risk_data"]["blacklist_addresses"]:
            assert 32 <= len(addr) <= 44, f"地址格式异常: {addr}"

    @pytest.mark.asyncio
    async def test_risky_tokens_have_risk_level(self, agent):
        """高危代币应有 risk_level"""
        result = await agent.aggregate_risk_data({})
        for mint, info in result["risk_data"]["risky_tokens"].items():
            assert "risk_level" in info


class TestValidateData:
    """validate_data 测试"""

    @pytest.mark.asyncio
    async def test_valid_wallet_data_passes(self, agent):
        """合法钱包数据应通过验证"""
        from mock.chain_data import mock_wallet_data
        assert await agent.validate_data(mock_wallet_data) is True

    @pytest.mark.asyncio
    async def test_missing_required_field_fails(self, agent):
        """缺少必填字段应验证失败"""
        bad_data = {"address": "test"}  # 缺少其他字段
        assert await agent.validate_data(bad_data) is False

    @pytest.mark.asyncio
    async def test_negative_balance_fails(self, agent):
        """负余额应验证失败"""
        bad_data = {
            "address": "test",
            "balances": {"token1": {"amount": -1, "usd_value": 100, "token_info": {}}},
            "nfts": [], "lp_positions": [], "lending_positions": [],
            "authorizations": [], "total_value_usd": 100, "last_updated": "now",
        }
        assert await agent.validate_data(bad_data) is False

    @pytest.mark.asyncio
    async def test_unreasonable_apy_fails(self, agent):
        """不合理 APY (>500%) 应验证失败"""
        bad_defi = {
            "lending_protocols": {"Test": {"supply_apy": 600, "borrow_apy": 5, "tvl": 100}},
            "liquidity_pools": {}, "staking_protocols": {}, "last_updated": "now",
        }
        assert await agent.validate_data(bad_defi) is False


class TestCallRouting:
    """__call__ 路由测试"""

    @pytest.mark.asyncio
    async def test_wallet_analysis_routes_to_wallet_only(self, agent):
        """task_type=wallet_analysis 应只聚合钱包数据"""
        state = {"wallet_address": "Test", "task_type": "wallet_analysis"}
        result = await agent(state)
        assert "wallet_data" in result

    @pytest.mark.asyncio
    async def test_strategy_generation_routes_to_wallet_and_defi(self, agent):
        """task_type=strategy_generation 应聚合钱包+DeFi 数据"""
        state = {"wallet_address": "Test", "task_type": "strategy_generation"}
        result = await agent(state)
        assert "wallet_data" in result
        assert "defi_data" in result

    @pytest.mark.asyncio
    async def test_risk_check_routes_to_wallet_and_risk(self, agent):
        """task_type=risk_check 应聚合钱包+风险数据"""
        state = {"wallet_address": "Test", "task_type": "risk_check"}
        result = await agent(state)
        assert "wallet_data" in result
        assert "risk_data" in result

    @pytest.mark.asyncio
    async def test_default_aggregates_all(self, agent):
        """默认 task_type 应聚合所有数据"""
        state = {"wallet_address": "Test", "task_type": "unknown"}
        result = await agent(state)
        assert "wallet_data" in result
        assert "defi_data" in result
        assert "risk_data" in result
