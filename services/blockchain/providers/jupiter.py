"""
Jupiter Aggregator 协议适配器

对接 Jupiter Swap API (v6 公共端点 / v1 API Key 端点)
- 报价查询：GET /quote
- 交易构建：POST /swap
- 代币价格：Jupiter Price API
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional

import httpx

from ..cache import cached
from ..config import config
from ..exceptions import ProviderError, QuoteError
from ..http_client import ResilientHTTPClient
from ..models.transaction import SwapQuote, SwapRoute
from .base import BaseDeFiProvider

logger = logging.getLogger(__name__)


class JupiterProvider(BaseDeFiProvider):
    """Jupiter 聚合交易协议适配器"""

    @property
    def protocol_name(self) -> str:
        return "jupiter"

    def __init__(self):
        self._base_url = config.JUPITER_API_URL
        self._api_key = config.JUPITER_API_KEY
        self._price_url = config.JUPITER_PRICE_URL

        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        # 使用带重试的 HTTP 客户端
        self._client = ResilientHTTPClient(
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0,
            headers=headers,
        )

    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> SwapQuote:
        """
        获取 Jupiter Swap 报价

        通过 Jupiter Quote API 获取最优兑换路由和报价
        """
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps,
            }

            response = await self._client.get(
                f"{self._base_url}/quote",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # 解析路由信息
            routes = []
            for route_plan in data.get("routePlan", []):
                swap_info = route_plan.get("swapInfo", {})
                routes.append(
                    SwapRoute(
                        protocol=swap_info.get("label", "Jupiter"),
                        input_mint=swap_info.get("inputMint", input_mint),
                        output_mint=swap_info.get("outputMint", output_mint),
                        in_amount=Decimal(str(swap_info.get("inAmount", amount))),
                        out_amount=Decimal(str(swap_info.get("outAmount", 0))),
                    )
                )

            quote = SwapQuote(
                provider="jupiter",
                input_mint=data.get("inputMint", input_mint),
                output_mint=data.get("outputMint", output_mint),
                in_amount=Decimal(str(data.get("inAmount", amount))),
                out_amount=Decimal(str(data.get("outAmount", 0))),
                price_impact_pct=Decimal(str(data.get("priceImpactPct", 0))),
                slippage_bps=slippage_bps,
                routes=routes,
                raw_quote=data,
            )

            logger.info(
                f"Jupiter 报价: {quote.in_amount} → {quote.out_amount} "
                f"(影响: {quote.price_impact_pct}%)"
            )
            return quote

        except httpx.HTTPStatusError as e:
            raise QuoteError("jupiter", f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise QuoteError("jupiter", str(e))

    async def build_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
    ) -> str:
        """
        通过 Jupiter Swap API 构建交易

        返回 base64 编码的交易数据，供前端签名
        """
        if not quote.raw_quote:
            raise ProviderError("jupiter", "报价数据缺失，无法构建交易")

        try:
            payload = {
                "quoteResponse": quote.raw_quote,
                "userPublicKey": user_public_key,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
            }

            response = await self._client.post(
                f"{self._base_url}/swap",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            swap_transaction = data.get("swapTransaction", "")
            if not swap_transaction:
                raise ProviderError("jupiter", "API 未返回交易数据")

            logger.info(f"Jupiter 交易构建成功 (用户: {user_public_key[:8]}...)")
            return swap_transaction

        except httpx.HTTPStatusError as e:
            raise ProviderError("jupiter", f"交易构建 HTTP {e.response.status_code}")
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError("jupiter", f"交易构建失败: {e}")

    @cached("jupiter_price", ttl=config.CACHE_TTL_TOKEN_PRICE)
    async def get_token_price(self, mint: str) -> Optional[Decimal]:
        """
        通过 Jupiter Price API 获取代币 USD 价格

        Args:
            mint: 代币 Mint 地址

        Returns:
            USD 价格，获取失败返回 None
        """
        try:
            response = await self._client.get(
                f"{self._price_url}",
                params={"ids": mint},
            )
            response.raise_for_status()
            data = response.json()

            token_data = data.get("data", {}).get(mint) or data.get(mint)
            if token_data:
                price = token_data.get("price") or token_data.get("usdPrice")
                if price:
                    return Decimal(str(price))
            return None

        except Exception as e:
            logger.warning(f"Jupiter 价格查询失败 [{mint[:8]}...]: {e}")
            return None

    @cached("jupiter_batch_price", ttl=config.CACHE_TTL_TOKEN_PRICE)
    async def batch_get_token_prices(self, mints: List[str]) -> Dict[str, Decimal]:
        """
        批量获取代币价格

        Args:
            mints: Mint 地址列表

        Returns:
            {mint: price_usd} 映射
        """
        if not mints:
            return {}

        try:
            ids_str = ",".join(mints)
            response = await self._client.get(
                f"{self._price_url}",
                params={"ids": ids_str},
            )
            response.raise_for_status()
            data = response.json()

            prices = {}
            for mint in mints:
                token_data = data.get("data", {}).get(mint) or data.get(mint)
                if token_data:
                    price = token_data.get("price") or token_data.get("usdPrice")
                    if price:
                        prices[mint] = Decimal(str(price))

            return prices

        except Exception as e:
            logger.warning(f"Jupiter 批量价格查询失败: {e}")
            return {}

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.close()
