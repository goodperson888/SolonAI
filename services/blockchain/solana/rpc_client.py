"""
Solana RPC客户端封装
提供与Solana区块链交互的基础功能
"""

import os
from typing import Any, Dict, List, Optional

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey
from solders.signature import Signature

class SolanaRPCClient:
    """Solana RPC客户端"""

    def __init__(self, rpc_url: Optional[str] = None):
        """
        初始化RPC客户端

        Args:
            rpc_url: RPC节点URL，默认使用环境变量SOLANA_RPC_URL
        """
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.client = AsyncClient(self.rpc_url, commitment=Confirmed)

    async def get_balance(self, address: str) -> float:
        """
        获取钱包SOL余额

        Args:
            address: 钱包地址

        Returns:
            SOL余额（单位：SOL）
        """
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_balance(pubkey)
            # 转换为SOL（1 SOL = 10^9 lamports）
            return response.value / 1e9
        except Exception as e:
            raise Exception(f"获取余额失败: {str(e)}")

    async def get_token_accounts(self, address: str) -> List[Dict[str, Any]]:
        """
        获取钱包的所有代币账户

        Args:
            address: 钱包地址

        Returns:
            代币账户列表
        """
        try:
            pubkey = Pubkey.from_string(address)
            response = await self.client.get_token_accounts_by_owner_json_parsed(
                pubkey,
                {"programId": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")},
            )

            accounts = []
            if response.value:
                for account in response.value:
                    info = account.account.data.parsed["info"]
                    accounts.append(
                        {
                            "mint": info["mint"],
                            "balance": float(info["tokenAmount"]["uiAmount"]),
                            "decimals": info["tokenAmount"]["decimals"],
                        }
                    )

            return accounts
        except Exception as e:
            raise Exception(f"获取代币账户失败: {str(e)}")

    async def get_transaction(self, signature: str) -> Optional[Dict[str, Any]]:
        """
        获取交易详情

        Args:
            signature: 交易签名

        Returns:
            交易详情
        """
        try:
            sig = Signature.from_string(signature)
            response = await self.client.get_transaction(sig, encoding="jsonParsed")

            if response.value:
                return {
                    "slot": response.value.slot,
                    "blockTime": response.value.block_time,
                    "meta": response.value.transaction.meta,
                    "transaction": response.value.transaction.transaction,
                }
            return None
        except Exception as e:
            raise Exception(f"获取交易失败: {str(e)}")

    async def send_transaction(self, signed_tx: bytes) -> str:
        """
        发送已签名的交易

        Args:
            signed_tx: 已签名的交易数据

        Returns:
            交易签名
        """
        try:
            response = await self.client.send_raw_transaction(signed_tx)
            return str(response.value)
        except Exception as e:
            raise Exception(f"发送交易失败: {str(e)}")

    async def close(self):
        """关闭客户端连接"""
        await self.client.close()
