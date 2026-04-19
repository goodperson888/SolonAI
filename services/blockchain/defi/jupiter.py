"""
Jupiter聚合交易协议集成
提供代币兑换、路由查询等功能
"""

from typing import Any, Dict, List

import httpx


class JupiterClient:
    """Jupiter聚合交易客户端"""

    BASE_URL = "https://quote-api.jup.ag/v6"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_quote(
        self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50
    ) -> Dict[str, Any]:
        """
        获取兑换报价

        Args:
            input_mint: 输入代币地址
            output_mint: 输出代币地址
            amount: 输入金额（最小单位）
            slippage_bps: 滑点容忍度（基点，50=0.5%）

        Returns:
            报价信息
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps,
            }

            response = await self.client.get(f"{self.BASE_URL}/quote", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取Jupiter报价失败: {str(e)}")

    async def get_swap_transaction(
        self, quote: Dict[str, Any], user_public_key: str
    ) -> Dict[str, Any]:
        """
        获取兑换交易数据

        Args:
            quote: 报价信息
            user_public_key: 用户钱包地址

        Returns:
            交易数据（需要用户签名）
        """
        try:
            payload = {
                "quoteResponse": quote,
                "userPublicKey": user_public_key,
                "wrapAndUnwrapSol": True,
            }

            response = await self.client.post(f"{self.BASE_URL}/swap", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取Jupiter交易数据失败: {str(e)}")

    async def get_token_list(self) -> List[Dict[str, Any]]:
        """
        获取支持的代币列表

        Returns:
            代币列表
        """
        try:
            response = await self.client.get("https://token.jup.ag/all")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取代币列表失败: {str(e)}")

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
