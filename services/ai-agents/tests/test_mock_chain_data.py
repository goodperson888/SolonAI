"""
TDD: Mock 数据层测试
验证 mock/chain_data.py 提供的数据结构和生成函数
"""

from mock.chain_data import (
    generate_mock_defi,
    generate_mock_risk,
    generate_mock_wallet,
    mock_defi_data,
    mock_risk_data,
    mock_strategy_data,
    mock_wallet_data,
)


class TestMockWalletData:
    """钱包 Mock 数据测试"""

    def test_has_required_top_level_fields(self):
        """mock_wallet_data 应包含所有顶层字段"""
        required = [
            "address",
            "balances",
            "nfts",
            "lp_positions",
            "lending_positions",
            "authorizations",
            "total_value_usd",
            "last_updated",
        ]
        for field in required:
            assert field in mock_wallet_data, f"缺少字段: {field}"

    def test_balances_is_dict_with_token_info(self):
        """balances 应为 dict，每个 token 包含 amount, usd_value, token_info"""
        assert isinstance(mock_wallet_data["balances"], dict)
        for mint, info in mock_wallet_data["balances"].items():
            assert "amount" in info, f"token {mint} 缺少 amount"
            assert "usd_value" in info, f"token {mint} 缺少 usd_value"
            assert "token_info" in info, f"token {mint} 缺少 token_info"

    def test_lending_positions_include_low_health(self):
        """lending_positions 应包含低健康因子场景（health < 1.2）"""
        positions = mock_wallet_data["lending_positions"]
        assert len(positions) > 0
        has_low_health = any(p.get("health", 999) < 1.2 for p in positions)
        assert has_low_health, "应包含低健康因子借贷仓位用于异常检测测试"

    def test_nfts_have_required_fields(self):
        """每个 NFT 应有 mint, name, collection, floor_price"""
        for nft in mock_wallet_data["nfts"]:
            for field in ["mint", "name", "collection", "floor_price"]:
                assert field in nft, f"NFT 缺少字段: {field}"

    def test_total_value_usd_is_positive(self):
        """total_value_usd 应为正数"""
        assert mock_wallet_data["total_value_usd"] > 0


class TestMockDefiData:
    """DeFi 协议 Mock 数据测试"""

    def test_has_required_top_level_fields(self):
        """mock_defi_data 应包含所有顶层字段"""
        required = ["lending_protocols", "liquidity_pools", "staking_protocols", "last_updated"]
        for field in required:
            assert field in mock_defi_data, f"缺少字段: {field}"

    def test_lending_protocols_have_marginfi(self):
        """lending_protocols 应包含 MarginFi"""
        assert "MarginFi" in mock_defi_data["lending_protocols"]

    def test_lending_protocol_has_supply_borrow_apy_tvl(self):
        """每个借贷协议应有 supply_apy, borrow_apy, tvl"""
        for name, info in mock_defi_data["lending_protocols"].items():
            assert "supply_apy" in info, f"{name} 缺少 supply_apy"
            assert "borrow_apy" in info, f"{name} 缺少 borrow_apy"
            assert "tvl" in info, f"{name} 缺少 tvl"

    def test_liquidity_pools_have_apy_tvl_volume(self):
        """每个流动性池应有 apy, tvl, volume_24h"""
        for pool_id, info in mock_defi_data["liquidity_pools"].items():
            assert "apy" in info, f"pool {pool_id} 缺少 apy"
            assert "tvl" in info, f"pool {pool_id} 缺少 tvl"
            assert "volume_24h" in info, f"pool {pool_id} 缺少 volume_24h"

    def test_at_least_3_lending_protocols(self):
        """至少应有 3 个借贷协议"""
        assert len(mock_defi_data["lending_protocols"]) >= 3

    def test_at_least_3_liquidity_pools(self):
        """至少应有 3 个流动性池"""
        assert len(mock_defi_data["liquidity_pools"]) >= 3


class TestMockRiskData:
    """风险 Mock 数据测试"""

    def test_has_required_top_level_fields(self):
        """mock_risk_data 应包含所有顶层字段"""
        required = [
            "blacklist_addresses",
            "risky_tokens",
            "phishing_patterns",
            "protocol_audits",
            "last_updated",
        ]
        for field in required:
            assert field in mock_risk_data, f"缺少字段: {field}"

    def test_blacklist_addresses_not_empty(self):
        """黑名单地址列表不应为空"""
        assert len(mock_risk_data["blacklist_addresses"]) > 0

    def test_risky_tokens_have_risk_info(self):
        """高危代币应有风险信息"""
        for mint, info in mock_risk_data["risky_tokens"].items():
            assert "risk_level" in info, f"token {mint} 缺少 risk_level"
            assert "reason" in info, f"token {mint} 缺少 reason"

    def test_protocol_audits_have_audit_info(self):
        """协议审计应有审计信息"""
        for protocol, info in mock_risk_data["protocol_audits"].items():
            assert "is_audited" in info, f"{protocol} 缺少 is_audited"


class TestMockStrategyData:
    """策略监控 Mock 数据测试"""

    def test_strategy_data_is_list(self):
        """mock_strategy_data 应为列表"""
        assert isinstance(mock_strategy_data, list)

    def test_has_active_warning_critical_status(self):
        """应包含 active, warning, critical 三种状态的策略"""
        statuses = {s["status"] for s in mock_strategy_data}
        assert "active" in statuses
        assert "warning" in statuses
        assert "critical" in statuses

    def test_strategy_has_required_fields(self):
        """每个策略应有必需字段"""
        required = [
            "strategy_id",
            "status",
            "current_value",
            "initial_value",
            "pnl",
            "pnl_percentage",
            "expected_apy",
            "actual_apy",
        ]
        for strategy in mock_strategy_data:
            for field in required:
                assert field in strategy, f"策略缺少字段: {field}"


class TestGenerateMockWallet:
    """generate_mock_wallet 动态生成测试"""

    def test_generates_with_custom_address(self):
        """应能按指定地址生成钱包数据"""
        addr = "CustomAddress123"
        wallet = generate_mock_wallet(address=addr)
        assert wallet["address"] == addr

    def test_generates_with_low_health(self):
        """应能生成包含低健康因子仓位的钱包数据"""
        wallet = generate_mock_wallet(include_low_health=True)
        has_low = any(p.get("health", 999) < 1.2 for p in wallet["lending_positions"])
        assert has_low

    def test_generates_without_low_health(self):
        """应能生成不包含低健康因子仓位的钱包数据"""
        wallet = generate_mock_wallet(include_low_health=False)
        for p in wallet["lending_positions"]:
            assert p.get("health", 999) >= 1.2


class TestGenerateMockDefi:
    """generate_mock_defi 动态生成测试"""

    def test_generates_with_custom_protocol_count(self):
        """应能按指定协议数量生成 DeFi 数据"""
        defi = generate_mock_defi(num_protocols=2)
        assert len(defi["lending_protocols"]) == 2

    def test_apy_values_are_reasonable(self):
        """APY 值应在合理范围（0-200%）"""
        for _name, info in generate_mock_defi()["lending_protocols"].items():
            assert 0 <= info["supply_apy"] <= 200
            assert 0 <= info["borrow_apy"] <= 200


class TestGenerateMockRisk:
    """generate_mock_risk 动态生成测试"""

    def test_generates_with_custom_blacklist_size(self):
        """应能按指定黑名单数量生成风险数据"""
        risk = generate_mock_risk(num_blacklist=5)
        assert len(risk["blacklist_addresses"]) == 5

    def test_default_blacklist_not_empty(self):
        """默认黑名单不应为空"""
        risk = generate_mock_risk()
        assert len(risk["blacklist_addresses"]) > 0
