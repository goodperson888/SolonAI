"""
代币信息与价格服务

通过 Jupiter Price API 提供代币价格查询
"""

import logging
from decimal import Decimal

from ..models.token import TokenPrice
from ..providers.jupiter import JupiterProvider

logger = logging.getLogger(__name__)


class TokenService:
    """代币信息与价格服务"""

    def __init__(self, jupiter: JupiterProvider | None = None):
        self._jupiter = jupiter or JupiterProvider()
        self._owns_client = jupiter is None

    async def get_token_price(self, mint: str, symbol: str | None = None) -> TokenPrice | None:
        """
        获取单个代币价格

        Args:
            mint: Mint 地址
            symbol: 可选符号

        Returns:
            代币价格信息，失败返回 None
        """
        price = await self._jupiter.get_token_price(mint)
        if price is not None:
            return TokenPrice(
                mint=mint,
                symbol=symbol,
                price_usd=price,
            )
        return None

    async def batch_get_token_prices(self, mints: list[str]) -> dict[str, TokenPrice]:
        """
        批量获取代币价格

        Args:
            mints: Mint 地址列表

        Returns:
            {mint: TokenPrice} 映射
        """
        prices = await self._jupiter.batch_get_token_prices(mints)

        result = {}
        for mint, price_usd in prices.items():
            result[mint] = TokenPrice(
                mint=mint,
                price_usd=price_usd,
            )

        return result

    async def get_sol_price(self) -> Decimal | None:
        """获取 SOL/USD 价格"""
        from ..config import config

        price = await self._jupiter.get_token_price(config.WRAPPED_SOL_MINT)
        return price

    async def close(self):
        """关闭连接"""
        if self._owns_client:
            await self._jupiter.close()
