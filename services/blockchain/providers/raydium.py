"""
Raydium AMM 协议适配器

对接 Raydium API:
- 数据 API: https://api-v3.raydium.io (池信息、代币列表)
- 交易 API: https://transaction-v1.raydium.io (swap 交易构建)
"""

import logging
from decimal import Decimal

import httpx

from ..cache import cached
from ..config import config
from ..exceptions import ProviderError, QuoteError
from ..http_client import ResilientHTTPClient
from ..models.transaction import SwapQuote, SwapRoute
from .base import BaseDeFiProvider

logger = logging.getLogger(__name__)


class RaydiumProvider(BaseDeFiProvider):
    """Raydium AMM 协议适配器"""

    @property
    def protocol_name(self) -> str:
        return "raydium"

    def __init__(self):
        self._api_url = config.RAYDIUM_API_URL
        self._trade_url = config.RAYDIUM_TRADE_URL
        # 使用带重试的 HTTP 客户端
        self._client = ResilientHTTPClient(
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0,
        )

    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> SwapQuote:
        """
        通过 Raydium Trade API 获取 Swap 报价

        使用 /compute/swap-base-in 端点
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps,
                "txVersion": "V0",
            }

            response = await self._client.get(
                f"{self._trade_url}/compute/swap-base-in",
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            # Raydium API 返回格式可能有 success/data 包装
            if isinstance(result, dict) and "data" in result:
                data = result["data"]
            else:
                data = result

            # 如果 API 返回了错误
            if isinstance(result, dict) and result.get("success") is False:
                error_msg = result.get("msg", "未知错误")
                raise QuoteError("raydium", error_msg)

            out_amount = int(data.get("outputAmount", data.get("outAmount", 0)))

            routes = [
                SwapRoute(
                    protocol="Raydium",
                    input_mint=input_mint,
                    output_mint=output_mint,
                    in_amount=Decimal(str(amount)),
                    out_amount=Decimal(str(out_amount)),
                )
            ]

            quote = SwapQuote(
                provider="raydium",
                input_mint=input_mint,
                output_mint=output_mint,
                in_amount=Decimal(str(amount)),
                out_amount=Decimal(str(out_amount)),
                price_impact_pct=Decimal(str(data.get("priceImpact", 0))),
                slippage_bps=slippage_bps,
                routes=routes,
                raw_quote=data,
            )

            logger.info(
                f"Raydium 报价: {quote.in_amount} → {quote.out_amount} "
                f"(影响: {quote.price_impact_pct}%)"
            )
            return quote

        except httpx.HTTPStatusError as e:
            raise QuoteError("raydium", f"HTTP {e.response.status_code}: {e.response.text}")
        except QuoteError:
            raise
        except Exception as e:
            raise QuoteError("raydium", str(e))

    async def build_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
    ) -> str:
        """
        通过 Raydium Trade API 构建 Swap 交易

        使用 /transaction/swap-base-in 端点
        """
        if not quote.raw_quote:
            raise ProviderError("raydium", "报价数据缺失")

        try:
            payload = {
                "computeUnitPriceMicroLamports": "1000",
                "swapResponse": quote.raw_quote,
                "txVersion": "V0",
                "wallet": user_public_key,
                "wrapSol": True,
                "unwrapSol": True,
            }

            response = await self._client.post(
                f"{self._trade_url}/transaction/swap-base-in",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict) and "data" in result:
                data = result["data"]
            else:
                data = result

            # Raydium 可能返回多个交易
            transactions = data if isinstance(data, list) else [data]
            if not transactions:
                raise ProviderError("raydium", "API 未返回交易数据")

            # 返回第一个交易的 base64 数据
            tx_data = transactions[0]
            if isinstance(tx_data, dict):
                swap_tx = tx_data.get("transaction", "")
            else:
                swap_tx = str(tx_data)

            logger.info(f"Raydium 交易构建成功 (用户: {user_public_key[:8]}...)")
            return swap_tx

        except httpx.HTTPStatusError as e:
            raise ProviderError("raydium", f"交易构建 HTTP {e.response.status_code}")
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("raydium", f"交易构建失败: {e}")

    @cached("raydium_pools", ttl=config.CACHE_TTL_DEFI_RATES)
    async def get_pool_list(self, page: int = 1, page_size: int = 100) -> list[dict]:
        """
        获取 Raydium 流动性池列表

        Returns:
            池列表
        """
        try:
            params = {
                "poolType": "all",
                "poolSortField": "volume24h",
                "sortType": "desc",
                "pageSize": page_size,
                "page": page,
            }
            response = await self._client.get(
                f"{self._api_url}/pools/info/list",
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return result.get("data", {}).get("data", [])
            return []

        except Exception as e:
            logger.warning(f"Raydium 池列表查询失败: {e}")
            return []

    async def get_pool_by_mints(self, mint1: str, mint2: str) -> list[dict]:
        """按代币对查询池信息"""
        try:
            params = {
                "mint1": mint1,
                "mint2": mint2,
                "poolType": "all",
                "poolSortField": "liquidity",
                "sortType": "desc",
                "pageSize": 10,
                "page": 1,
            }
            response = await self._client.get(
                f"{self._api_url}/pools/info/mint",
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                return result.get("data", {}).get("data", [])
            return []

        except Exception as e:
            logger.warning(f"Raydium 池查询失败: {e}")
            return []

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.close()
