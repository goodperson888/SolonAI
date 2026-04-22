"""
Blockchain Service
区块链交互服务，提供 Solana 链上操作和 DeFi 协议集成

重构后的分层架构：
- transport/     传输层（RPC 客户端）
- providers/     协议适配层（Jupiter, Raydium）
- services/      业务抽象层（钱包、代币、交易）
- models/        数据模型（Pydantic）
"""

from .config import config
from .providers.jupiter import JupiterProvider
from .providers.marginfi import MarginFiProvider
from .providers.raydium import RaydiumProvider
from .services.token_service import TokenService
from .services.transaction_service import TransactionService
from .services.wallet_service import WalletService
from .transport.rpc_client import EnhancedRPCClient

__all__ = [
    "config",
    "EnhancedRPCClient",
    "JupiterProvider",
    "RaydiumProvider",
    "MarginFiProvider",
    "WalletService",
    "TokenService",
    "TransactionService",
]
