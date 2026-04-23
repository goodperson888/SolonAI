"""
DeFi 协议适配器基类

定义所有 DeFi 协议适配器必须实现的统一接口
"""

from abc import ABC, abstractmethod

from ..models.transaction import SwapQuote


class BaseDeFiProvider(ABC):
    """DeFi 协议适配器基类"""

    @property
    @abstractmethod
    def protocol_name(self) -> str:
        """协议名称"""

    @abstractmethod
    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> SwapQuote:
        """
        获取 Swap 报价

        Args:
            input_mint: 输入代币 Mint 地址
            output_mint: 输出代币 Mint 地址
            amount: 输入数量（最小单位，如 lamports）
            slippage_bps: 滑点容忍度（基点，50 = 0.5%）

        Returns:
            报价信息
        """

    @abstractmethod
    async def build_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
    ) -> str:
        """
        构建 Swap 交易

        Args:
            quote: 报价信息（从 get_swap_quote 获取）
            user_public_key: 用户钱包地址

        Returns:
            Base64 编码的未签名交易
        """

    @abstractmethod
    async def close(self):
        """关闭客户端连接"""
