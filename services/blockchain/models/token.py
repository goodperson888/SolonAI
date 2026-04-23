"""
代币信息数据模型
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TokenInfo(BaseModel):
    """代币元数据"""

    mint: str = Field(description="Mint 地址")
    symbol: str = Field(description="符号")
    name: str = Field(default="", description="名称")
    decimals: int = Field(default=9, description="小数位数")
    logo_url: Optional[str] = Field(default=None, description="Logo URL")


class TokenPrice(BaseModel):
    """代币价格"""

    mint: str = Field(description="Mint 地址")
    symbol: Optional[str] = Field(default=None, description="符号")
    price_usd: Decimal = Field(description="USD 价格")
    price_change_24h: Optional[Decimal] = Field(default=None, description="24h 涨跌幅 (%)")
