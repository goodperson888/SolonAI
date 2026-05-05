from __future__ import annotations

from typing import Any, Dict

from app.core.config import settings


def is_demo_mode_enabled() -> bool:
    return bool(settings.SOLON_DEMO_MODE)


def build_demo_wallet_assets(wallet_address: str, network: str) -> Dict[str, Any]:
    sol_price = 85.31
    sol_balance = 5.0 if network == "mainnet" else 12.5
    usdc_balance = 1200.0 if network == "mainnet" else 350.0
    usdc_price = 1.0

    tokens = [
        {
            "symbol": "USDC",
            "name": "USD Coin",
            "mint": (
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                if network == "mainnet"
                else "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
            ),
            "balance": usdc_balance,
            "price_usd": usdc_price,
            "value_usd": usdc_balance * usdc_price,
        }
    ]
    total_value = sol_balance * sol_price + sum(token["value_usd"] for token in tokens)

    return {
        "wallet_address": wallet_address,
        "sol_balance": sol_balance,
        "sol_price_usd": sol_price,
        "sol_value_usd": sol_balance * sol_price,
        "tokens": tokens,
        "total_value_usd": total_value,
        "queried_network": network,
        "alternate_network": None,
        "alternate_sol_balance": None,
        "network_hint": "当前处于 DEMO 演示模式，资产与收益数据为本地示例数据，用于走通界面和交互流程。",
    }


def build_demo_diagnosis(wallet_address: str) -> Dict[str, Any]:
    return {
        "wallet_address": wallet_address,
        "risk_level": "low",
        "risk_score": 28.0,
        "issues": [
            {
                "type": "演示模式",
                "severity": "low",
                "description": "当前结果来自本地演示数据，不代表真实链上资产分布。",
                "recommendation": "切换回真实模式后，再用真实钱包重新做一次诊断。",
            },
            {
                "type": "资产集中度",
                "severity": "low",
                "description": "示例组合中 SOL 占比较高，适合作为保守型 DeFi 存款策略演示。",
                "recommendation": "如用于真实投资，建议增加稳定币仓位降低波动。",
            },
        ],
        "health_metrics": {
            "diversification_score": 62.0,
            "liquidity_score": 88.0,
            "volatility_score": 46.0,
        },
    }


def build_demo_pnl(wallet_address: str) -> Dict[str, Any]:
    return {
        "wallet_address": wallet_address,
        "total_pnl": 18.42,
        "total_pnl_percentage": 1.13,
        "realized_pnl": 6.25,
        "unrealized_pnl": 12.17,
        "roi_percentage": 1.13,
        "breakdown": [
            {
                "asset": "SOL",
                "type": "MarginFi 存款收益",
                "pnl": 8.91,
                "percentage": 1.8,
            },
            {
                "asset": "USDC",
                "type": "Raydium LP 收益预估",
                "pnl": 9.51,
                "percentage": 0.79,
            },
        ],
    }


def build_protocol_capabilities(demo_mode: bool) -> Dict[str, Any]:
    return {
        "demo_mode": demo_mode,
        "summary": {
            "real_execution_supported": ["jupiter_swap", "raydium_swap"],
            "preview_only": ["marginfi_lending", "solend_lending"],
            "market_data_only": ["kamino", "orca"],
        },
        "protocols": {
            "jupiter": {
                "market_data": True,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": True,
                "wallet_signature": True,
                "notes": "当前只在主网 swap 路径下支持生成真实待签名交易。",
            },
            "raydium": {
                "market_data": True,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": True,
                "wallet_signature": True,
                "notes": "当前以 swap 为主，LP/加池执行仍偏预览化。",
            },
            "marginfi": {
                "market_data": True,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": False,
                "wallet_signature": False,
                "notes": "已支持真实池/APY读取，但存借交易执行仍是参数预览，未接完整协议 SDK。",
            },
            "solend": {
                "market_data": False,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": False,
                "wallet_signature": False,
                "notes": "当前主要用于策略建议与预览，不具备真实执行链路。",
            },
            "kamino": {
                "market_data": False,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": False,
                "wallet_signature": False,
                "notes": "目前仅策略层引用，协议数据和执行链路未完整接通。",
            },
            "orca": {
                "market_data": False,
                "strategy_generation": True,
                "devnet_execution": False,
                "mainnet_execution": False,
                "wallet_signature": False,
                "notes": "目前仅保留 mock/规划位，未接入正式 provider。",
            },
        },
        "testing_guidance": {
            "works_well_on_devnet_or_demo": [
                "钱包连接与网络切换",
                "资产卡片展示",
                "AI 问答与策略卡片流式展示",
                "策略保存到工作台",
                "执行前参数确认与风控提示",
            ],
            "requires_mainnet_for_real_validation": [
                "Jupiter/Raydium 真实报价差异",
                "真实可签名 swap 交易构建",
                "真实钱包签名与链上广播",
                "真实池子流动性、滑点、价格影响",
            ],
            "best_demo_approach": "日常开发先开 SOLON_DEMO_MODE=1 走完整演示流程；验证真实签名时，再切主网并仅测试 Jupiter/Raydium swap 路径。",
        },
    }
