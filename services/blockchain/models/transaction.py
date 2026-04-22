"""
交易相关数据模型
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class SwapRoute(BaseModel):
    """Swap 路由步骤"""

    protocol: str = Field(description="协议名称")
    input_mint: str = Field(description="输入代币 Mint")
    output_mint: str = Field(description="输出代币 Mint")
    in_amount: Decimal = Field(description="输入数量")
    out_amount: Decimal = Field(description="输出数量")


class SwapQuote(BaseModel):
    """Swap 报价"""

    provider: str = Field(description="报价来源 (jupiter/raydium)")
    input_mint: str = Field(description="输入代币 Mint")
    output_mint: str = Field(description="输出代币 Mint")
    in_amount: Decimal = Field(description="输入数量（最小单位）")
    out_amount: Decimal = Field(description="预期输出数量（最小单位）")
    in_amount_human: Decimal | None = Field(default=None, description="输入数量（人类可读）")
    out_amount_human: Decimal | None = Field(default=None, description="输出数量（人类可读）")
    price_impact_pct: Decimal | None = Field(default=None, description="价格影响 (%)")
    slippage_bps: int = Field(default=50, description="滑点容忍度（基点）")
    routes: list[SwapRoute] = Field(default_factory=list, description="路由详情")
    raw_quote: dict | None = Field(default=None, description="原始报价数据（用于构建交易）")


class TransactionStatus(str, Enum):
    """交易状态"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"
    FAILED = "failed"


class TransactionResult(BaseModel):
    """交易结果"""

    signature: str = Field(description="交易签名")
    status: TransactionStatus = Field(description="交易状态")
    slot: int | None = Field(default=None, description="确认 Slot")
    error: str | None = Field(default=None, description="错误信息")
    serialized_transaction: str | None = Field(default=None, description="Base64 编码的未签名交易（供前端签名）")
