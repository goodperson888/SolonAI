"""
Mock 链上数据层
提供 Solana 链上数据的 Mock 数据集，用于开发和测试 AI Agent
"""

from datetime import datetime
from typing import Dict, List, Optional

# ============================================================
# 静态 Mock 数据集
# ============================================================

mock_wallet_data: Dict = {
    "address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "balances": {
        "So11111111111111111111111111111111111111112": {
            "amount": 15.5,
            "usd_value": 2325.0,
            "token_info": {"symbol": "SOL", "name": "Solana", "decimals": 9},
        },
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
            "amount": 1000.0,
            "usd_value": 1000.0,
            "token_info": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
        },
        "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {
            "amount": 5.0,
            "usd_value": 750.0,
            "token_info": {"symbol": "mSOL", "name": "Marinade staked SOL", "decimals": 9},
        },
        "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn": {
            "amount": 0.0,
            "usd_value": 0.0,
            "token_info": {"symbol": "jitoSOL", "name": "Jito Staked SOL", "decimals": 9},
        },
    },
    "nfts": [
        {
            "mint": "Dz3fFqQJ9VpDZtBpPmFVzCvW9Hq7T1vM2kLxRnGhYaB",
            "name": "DeGod #1234",
            "collection": "DeGods",
            "floor_price": 2.5,
        },
        {
            "mint": "Ak4gQqRJ0WqEaUcCqNgWwAxIs2T3uN3mL4sSoThIzBc",
            "name": "Tensorians #567",
            "collection": "Tensorians",
            "floor_price": 0.8,
        },
    ],
    "lp_positions": [
        {
            "protocol": "Raydium",
            "pool": "SOL-USDC",
            "amount": 1.5,
            "value": 300.0,
        },
    ],
    "lending_positions": [
        {
            "protocol": "MarginFi",
            "supplied": {"SOL": 5.0},
            "borrowed": {"USDC": 300.0},
            "health": 1.85,
        },
        {
            "protocol": "MarginFi",
            "supplied": {"USDC": 200.0},
            "borrowed": {"SOL": 1.2},
            "health": 1.05,  # 低健康因子，用于异常检测测试
        },
    ],
    "authorizations": [
        {"program": "Jupiter", "authority": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4", "risk_level": "low"},
        {"program": "Unknown DEX", "authority": "UnknownProgram1111111111111111111111111", "risk_level": "high"},
    ],
    "total_value_usd": 4375.0,
    "last_updated": datetime.now().isoformat(),
}

mock_defi_data: Dict = {
    "lending_protocols": {
        "MarginFi": {"supply_apy": 3.5, "borrow_apy": 5.2, "tvl": 580_000_000},
        "Kamino": {"supply_apy": 4.1, "borrow_apy": 6.0, "tvl": 320_000_000},
        "Solend": {"supply_apy": 2.8, "borrow_apy": 4.5, "tvl": 250_000_000},
    },
    "liquidity_pools": {
        "raydium-SOL-USDC": {"apy": 12.5, "tvl": 45_000_000, "volume_24h": 8_500_000},
        "orca-SOL-mSOL": {"apy": 8.3, "tvl": 22_000_000, "volume_24h": 3_200_000},
        "meteora-USDC-USDT": {"apy": 5.1, "tvl": 80_000_000, "volume_24h": 15_000_000},
    },
    "staking_protocols": {
        "Marinade": {"apy": 6.8, "tvl": 1_200_000_000, "lock_period": "none"},
        "Jito": {"apy": 7.1, "tvl": 950_000_000, "lock_period": "none"},
    },
    "last_updated": datetime.now().isoformat(),
}

mock_risk_data: Dict = {
    "blacklist_addresses": {
        "Scam1111111111111111111111111111111111",
        "RugP22222222222222222222222222222222222",
        "Phsh33333333333333333333333333333333333",
    },
    "risky_tokens": {
        "Bscam11111111111111111111111111111111111111111": {
            "risk_level": "critical",
            "reason": "已确认 rug pull 项目",
        },
        "Csuspect222222222222222222222222222222222222222": {
            "risk_level": "high",
            "reason": "疑似钓鱼代币，无法出售",
        },
    },
    "phishing_patterns": [
        "airdrop_claim_fake_site",
        "fake_wallet_extension",
        "impersonation_dm",
    ],
    "protocol_audits": {
        "MarginFi": {"is_audited": True, "auditor": "OtterSec", "audit_date": "2024-01-15"},
        "Jupiter": {"is_audited": True, "auditor": "Trail of Bits", "audit_date": "2024-03-01"},
        "UnknownProtocol": {"is_audited": False, "auditor": None, "audit_date": None},
    },
    "last_updated": datetime.now().isoformat(),
}

mock_strategy_data: List[Dict] = [
    {
        "strategy_id": "strat_001",
        "status": "active",
        "current_value": 1050.0,
        "initial_value": 1000.0,
        "pnl": 50.0,
        "pnl_percentage": 5.0,
        "expected_apy": 12.5,
        "actual_apy": 13.1,
        "alerts": [],
        "suggestions": [],
        "last_checked": datetime.now().isoformat(),
    },
    {
        "strategy_id": "strat_002",
        "status": "warning",
        "current_value": 920.0,
        "initial_value": 1000.0,
        "pnl": -80.0,
        "pnl_percentage": -8.0,
        "expected_apy": 10.0,
        "actual_apy": 3.5,
        "alerts": [
            {"type": "apy_drift", "severity": "warning", "message": "实际 APY 严重低于预期"},
        ],
        "suggestions": ["考虑调仓到更高 APY 的协议"],
        "last_checked": datetime.now().isoformat(),
    },
    {
        "strategy_id": "strat_003",
        "status": "critical",
        "current_value": 850.0,
        "initial_value": 1000.0,
        "pnl": -150.0,
        "pnl_percentage": -15.0,
        "expected_apy": 8.0,
        "actual_apy": -45.0,
        "alerts": [
            {"type": "stop_loss", "severity": "critical", "message": "触发止损线"},
            {"type": "lending_risk", "severity": "critical", "message": "借贷健康度过低"},
        ],
        "suggestions": ["立即补充抵押品或偿还部分借款"],
        "last_checked": datetime.now().isoformat(),
    },
]


# ============================================================
# 动态生成函数
# ============================================================

def generate_mock_wallet(
    address: str = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    include_low_health: bool = True,
) -> Dict:
    """
    动态生成钱包 Mock 数据

    Args:
        address: 钱包地址
        include_low_health: 是否包含低健康因子借贷仓位

    Returns:
        钱包数据字典
    """
    import copy
    wallet = copy.deepcopy(mock_wallet_data)
    wallet["address"] = address

    if not include_low_health:
        wallet["lending_positions"] = [
            p for p in wallet["lending_positions"] if p.get("health", 999) >= 1.2
        ]
        if not wallet["lending_positions"]:
            wallet["lending_positions"] = [
                {"protocol": "MarginFi", "supplied": {"SOL": 10.0}, "borrowed": {"USDC": 500.0}, "health": 2.5},
            ]
    return wallet


def generate_mock_defi(num_protocols: Optional[int] = None) -> Dict:
    """
    动态生成 DeFi 协议 Mock 数据

    Args:
        num_protocols: 借贷协议数量，None 表示全部

    Returns:
        DeFi 数据字典
    """
    import copy
    defi = copy.deepcopy(mock_defi_data)

    if num_protocols is not None:
        protocols = list(defi["lending_protocols"].items())[:num_protocols]
        defi["lending_protocols"] = dict(protocols)

    return defi


def generate_mock_risk(num_blacklist: Optional[int] = None) -> Dict:
    """
    动态生成风险 Mock 数据

    Args:
        num_blacklist: 黑名单地址数量，None 表示全部

    Returns:
        风险数据字典
    """
    import copy
    risk = copy.deepcopy(mock_risk_data)

    if num_blacklist is not None:
        addresses = list(risk["blacklist_addresses"])
        # 如果请求数量超过已有数量，生成额外地址
        while len(addresses) < num_blacklist:
            idx = len(addresses)
            addresses.append(f"FakeAddr{idx:040d}")
        risk["blacklist_addresses"] = set(addresses[:num_blacklist])

    return risk
