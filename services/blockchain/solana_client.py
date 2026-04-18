"""
Solana 区块链客户端

提供与 Solana 链交互的基础功能：
- 钱包余额查询（SOL + SPL Token）
- 交易构建与发送
- 链上数据查询
"""

import os
from typing import Dict, List, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID


class SolanaClient:
    """Solana 区块链客户端"""

    def __init__(self, rpc_url: Optional[str] = None):
        """
        初始化 Solana 客户端

        Args:
            rpc_url: Solana RPC 节点地址，默认使用 Devnet
        """
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        self.client = AsyncClient(self.rpc_url, commitment=Confirmed)

    async def get_sol_balance(self, wallet_address: str) -> float:
        """
        获取钱包 SOL 余额

        Args:
            wallet_address: 钱包地址

        Returns:
            SOL 余额（单位：SOL）
        """
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_balance(pubkey)
            # lamports 转 SOL (1 SOL = 10^9 lamports)
            balance_sol = response.value / 1_000_000_000
            return balance_sol
        except Exception as e:
            print(f"获取 SOL 余额失败: {e}")
            return 0.0

    async def get_token_accounts(self, wallet_address: str) -> List[Dict]:
        """
        获取钱包所有 SPL Token 账户

        Args:
            wallet_address: 钱包地址

        Returns:
            Token 账户列表
        """
        try:
            pubkey = Pubkey.from_string(wallet_address)
            response = await self.client.get_token_accounts_by_owner(
                pubkey,
                {"programId": TOKEN_PROGRAM_ID},
            )

            token_accounts = []
            if response.value:
                for account in response.value:
                    # 解析 Token 账户数据
                    account_data = account.account.data
                    token_accounts.append(
                        {
                            "pubkey": str(account.pubkey),
                            "data": account_data,
                        }
                    )

            return token_accounts
        except Exception as e:
            print(f"获取 Token 账户失败: {e}")
            return []

    async def get_token_balance(self, wallet_address: str, token_mint: str) -> Optional[float]:
        """
        获取指定 Token 的余额

        Args:
            wallet_address: 钱包地址
            token_mint: Token Mint 地址

        Returns:
            Token 余额
        """
        try:
            # 获取 token accounts（暂未使用，待实现）
            # token_accounts = await self.get_token_accounts(wallet_address)

            # 这里需要解析 token account data 来获取余额
            # 简化实现：返回 None 表示需要进一步实现
            # 实际项目中需要使用 spl-token 库解析账户数据

            return None
        except Exception as e:
            print(f"获取 Token 余额失败: {e}")
            return None

    async def get_wallet_assets(self, wallet_address: str) -> Dict:
        """
        获取钱包所有资产（SOL + Tokens）

        Args:
            wallet_address: 钱包地址

        Returns:
            资产信息字典
        """
        try:
            # 获取 SOL 余额
            sol_balance = await self.get_sol_balance(wallet_address)

            # 获取 Token 账户
            token_accounts = await self.get_token_accounts(wallet_address)

            return {
                "wallet_address": wallet_address,
                "sol_balance": sol_balance,
                "token_accounts_count": len(token_accounts),
                "token_accounts": token_accounts,
            }
        except Exception as e:
            print(f"获取钱包资产失败: {e}")
            return {
                "wallet_address": wallet_address,
                "sol_balance": 0.0,
                "token_accounts_count": 0,
                "token_accounts": [],
            }

    async def close(self):
        """关闭客户端连接"""
        await self.client.close()


# 常用 Token Mint 地址（Devnet）
COMMON_TOKENS = {
    "USDC": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
    "USDT": "EJwZgeZrdC8TXTQbQBoL6bfuAnFUUy1PVCMB4DYPzVaS",  # Devnet USDT
}
