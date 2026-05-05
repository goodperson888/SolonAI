"""
Solana RPC 模块配置

管理 RPC 端点、API Key、超时、缓存 TTL 等配置
"""

import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


class SolanaConfig:
    """Solana RPC 配置"""

    # ---- 网络 ----
    NETWORK: str = os.getenv("SOLANA_NETWORK", "mainnet")

    # ---- RPC 端点（按优先级排列） ----
    RPC_ENDPOINTS: List[str] = [
        url.strip()
        for url in os.getenv(
            "SOLANA_RPC_URLS",
            os.getenv(
                "SOLANA_RPC_URL",
                "https://api.mainnet-beta.solana.com,https://solana-rpc.publicnode.com",
            ),
        ).split(",")
        if url.strip()
    ]

    # ---- 超时与重试 ----
    RPC_TIMEOUT: int = int(os.getenv("RPC_TIMEOUT", "30"))
    RPC_MAX_RETRIES: int = int(os.getenv("RPC_MAX_RETRIES", "3"))
    RPC_RETRY_DELAY: float = float(os.getenv("RPC_RETRY_DELAY", "1.0"))

    # ---- Jupiter 配置 ----
    JUPITER_API_KEY: str = os.getenv("JUPITER_API_KEY", "")
    JUPITER_API_URL: str = os.getenv("JUPITER_API_URL", "https://lite-api.jup.ag/swap/v1")
    JUPITER_PRICE_URL: str = os.getenv("JUPITER_PRICE_URL", "https://lite-api.jup.ag/price/v3")

    # ---- Raydium 配置 ----
    RAYDIUM_API_URL: str = os.getenv("RAYDIUM_API_URL", "https://api-v3.raydium.io")
    RAYDIUM_TRADE_URL: str = os.getenv("RAYDIUM_TRADE_URL", "https://transaction-v1.raydium.io")

    # ---- 缓存 TTL (秒) ----
    CACHE_TTL_BALANCE: int = 30
    CACHE_TTL_TOKENS: int = 60
    CACHE_TTL_TOKEN_META: int = 3600
    CACHE_TTL_TOKEN_PRICE: int = 30
    CACHE_TTL_DEFI_RATES: int = 120

    # ---- 默认滑点（基点） ----
    DEFAULT_SLIPPAGE_BPS: int = int(os.getenv("DEFAULT_SLIPPAGE_BPS", "50"))

    # ---- 常用代币 Mint 地址 ----
    WRAPPED_SOL_MINT: str = "So11111111111111111111111111111111111111112"

    # Mainnet 代币
    MAINNET_TOKENS: Dict[str, str] = {
        "SOL": "So11111111111111111111111111111111111111112",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    }

    # Devnet 代币
    DEVNET_TOKENS: Dict[str, str] = {
        "SOL": "So11111111111111111111111111111111111111112",
        "USDC": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
        "USDT": "EJwZgeZrdC8TXTQbQBoL6bfuAnFUUy1PVCMB4DYPzVaS",
    }

    @classmethod
    def get_tokens(cls, network: str | None = None) -> Dict[str, str]:
        """根据当前网络返回代币地址映射"""
        active_network = network or cls.NETWORK
        if active_network == "devnet":
            return cls.DEVNET_TOKENS
        return cls.MAINNET_TOKENS

    @classmethod
    def get_primary_rpc(cls, network: str | None = None) -> str:
        """获取主 RPC 端点"""
        if network == "devnet":
            return "https://api.devnet.solana.com"
        return cls.RPC_ENDPOINTS[0] if cls.RPC_ENDPOINTS else "https://api.devnet.solana.com"

    @classmethod
    def get_rpc_endpoints(cls, network: str | None = None) -> List[str]:
        """根据网络返回 RPC 列表。"""
        active_network = network or cls.NETWORK
        if active_network == "devnet":
            return ["https://api.devnet.solana.com"]
        return cls.RPC_ENDPOINTS


config = SolanaConfig()
