"""
交易构建与发送服务

聚合 Jupiter / Raydium 报价，构建 swap 交易，发送到链上
"""

import logging

from ..exceptions import ProviderError, QuoteError
from ..models.transaction import SwapQuote, TransactionResult, TransactionStatus
from ..providers.jupiter import JupiterProvider
from ..providers.raydium import RaydiumProvider
from ..transport.rpc_client import EnhancedRPCClient
from ..utils.transaction_builder import TransactionBuilder

logger = logging.getLogger(__name__)


class TransactionService:
    """交易构建与发送服务"""

    def __init__(
        self,
        rpc_client: EnhancedRPCClient | None = None,
        jupiter: JupiterProvider | None = None,
        raydium: RaydiumProvider | None = None,
    ):
        self._rpc = rpc_client or EnhancedRPCClient()
        self._jupiter = jupiter or JupiterProvider()
        self._raydium = raydium or RaydiumProvider()
        self._owns_clients = rpc_client is None

    async def get_swap_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
        provider: str = "auto",
    ) -> SwapQuote:
        """
        获取 Swap 报价

        Args:
            input_mint: 输入代币 Mint
            output_mint: 输出代币 Mint
            amount: 输入数量（最小单位）
            slippage_bps: 滑点（基点）
            provider: 指定协议 ("jupiter" / "raydium" / "auto")

        Returns:
            最优报价
        """
        if provider == "jupiter":
            return await self._jupiter.get_swap_quote(input_mint, output_mint, amount, slippage_bps)

        if provider == "raydium":
            return await self._raydium.get_swap_quote(input_mint, output_mint, amount, slippage_bps)

        # auto: 同时查询两个协议，返回最优报价
        return await self._get_best_quote(input_mint, output_mint, amount, slippage_bps)

    async def _get_best_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
    ) -> SwapQuote:
        """聚合多个协议报价，返回最优"""
        import asyncio

        quotes: list[SwapQuote] = []
        errors: list[str] = []

        # 并发获取报价
        tasks = [
            self._safe_get_quote(self._jupiter, input_mint, output_mint, amount, slippage_bps),
            self._safe_get_quote(self._raydium, input_mint, output_mint, amount, slippage_bps),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            if isinstance(result, SwapQuote):
                quotes.append(result)
            elif isinstance(result, str):
                errors.append(result)

        if not quotes:
            error_details = "; ".join(errors) if errors else "所有协议均无可用报价"
            raise QuoteError("aggregator", error_details)

        # 选择输出最多的报价
        best = max(quotes, key=lambda q: q.out_amount)
        logger.info(f"最优报价由 {best.provider} 提供: {best.in_amount} → {best.out_amount}")
        return best

    @staticmethod
    async def _safe_get_quote(provider, *args) -> SwapQuote | str:
        """安全获取报价，失败返回错误信息"""
        try:
            return await provider.get_swap_quote(*args)
        except Exception as e:
            return f"{provider.protocol_name}: {e}"

    async def build_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
    ) -> str:
        """
        构建 Swap 交易

        Args:
            quote: 报价信息
            user_public_key: 用户钱包地址

        Returns:
            Base64 编码的未签名交易
        """
        if quote.provider == "jupiter":
            return await self._jupiter.build_swap_transaction(quote, user_public_key)
        elif quote.provider == "raydium":
            return await self._raydium.build_swap_transaction(quote, user_public_key)
        else:
            raise ProviderError(quote.provider, "不支持的协议")

    async def send_signed_transaction(self, signed_tx_base64: str) -> TransactionResult:
        """
        发送已签名交易

        Args:
            signed_tx_base64: Base64 编码的已签名交易

        Returns:
            交易结果
        """
        import base64

        try:
            tx_bytes = base64.b64decode(signed_tx_base64, validate=True)
        except ValueError as exc:
            raise ValueError("signed_tx_base64 不是有效的 Base64 已签名交易") from exc

        if not tx_bytes:
            raise ValueError("signed_tx_base64 不能为空")

        signature = await self._rpc.send_raw_transaction(tx_bytes)

        return TransactionResult(
            signature=signature,
            status=TransactionStatus.PENDING,
        )

    async def parse_transaction(self, transaction_base64: str) -> dict:
        """解析序列化交易结构和签名。"""
        return TransactionBuilder.parse_transaction(transaction_base64)

    async def parse_transaction_signatures(self, transaction_base64: str) -> dict:
        """解析序列化交易签名。"""
        return TransactionBuilder.parse_signatures(transaction_base64)

    async def estimate_transaction_cost(self, transaction_base64: str) -> dict:
        """估算交易费用，并尽可能返回模拟消耗。"""
        parsed = TransactionBuilder.parse_transaction(transaction_base64)
        fee = await self._rpc.estimate_fee_for_transaction(transaction_base64)

        simulation = None
        try:
            simulation = await self._rpc.simulate_transaction(transaction_base64)
        except Exception as exc:
            simulation = {"error": str(exc)}

        return {
            "fee": fee,
            "simulation": simulation,
            "transaction": {
                "version": parsed["version"],
                "size_bytes": parsed["size_bytes"],
                "required_signatures": parsed["required_signatures"],
                "signed": parsed["signed"],
                "instruction_count": len(parsed["instructions"]),
            },
        }

    async def pack_batch_transactions(
        self,
        instructions: list[dict],
        payer: str,
        recent_blockhash: str | None = None,
        max_instructions_per_tx: int = 8,
        max_tx_size_bytes: int = 1232,
        compute_unit_limit: int | None = None,
        compute_unit_price_micro_lamports: int | None = None,
    ) -> list[dict]:
        """将多条指令按大小和数量打包为多笔未签名 v0 交易。"""
        blockhash = recent_blockhash or await self._rpc.get_latest_blockhash()
        parsed_instructions = [
            TransactionBuilder.instruction_from_payload(instruction) for instruction in instructions
        ]
        packed = TransactionBuilder.pack_instructions(
            instructions=parsed_instructions,
            payer=payer,
            recent_blockhash=blockhash,
            max_instructions_per_tx=max_instructions_per_tx,
            max_tx_size_bytes=max_tx_size_bytes,
            compute_unit_limit=compute_unit_limit,
            compute_unit_price_micro_lamports=compute_unit_price_micro_lamports,
        )
        return [
            {
                "transaction_base64": item.transaction_base64,
                "transaction_index": item.transaction_index,
                "instruction_count": item.instruction_count,
                "size_bytes": item.size_bytes,
                "required_signatures": item.required_signatures,
                "recent_blockhash": item.recent_blockhash,
            }
            for item in packed
        ]

    async def get_transaction_history(
        self,
        wallet_address: str,
        limit: int = 20,
        before: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        """查询钱包链上交易签名历史。"""
        safe_limit = max(1, min(limit, 100))
        return await self._rpc.get_transaction_history(
            wallet_address,
            limit=safe_limit,
            before=before,
            until=until,
        )

    async def get_transaction_status(self, signature: str) -> TransactionResult:
        """查询交易状态"""
        try:
            signature_status = await self._rpc.get_signature_status(signature)
            if signature_status:
                if signature_status.get("err"):
                    return TransactionResult(
                        signature=signature,
                        status=TransactionStatus.FAILED,
                        slot=signature_status.get("slot"),
                        error=str(signature_status.get("err")),
                    )

                confirmation_status = (signature_status.get("confirmation_status") or "").lower()
                if "finalized" in confirmation_status:
                    status = TransactionStatus.FINALIZED
                elif "confirmed" in confirmation_status:
                    status = TransactionStatus.CONFIRMED
                else:
                    status = TransactionStatus.PENDING

                return TransactionResult(
                    signature=signature,
                    status=status,
                    slot=signature_status.get("slot"),
                )

            tx_info = await self._rpc.get_transaction(signature)
            if tx_info:
                return TransactionResult(
                    signature=signature,
                    status=TransactionStatus.CONFIRMED,
                    slot=tx_info.get("slot"),
                )

            return TransactionResult(
                signature=signature,
                status=TransactionStatus.PENDING,
            )
        except Exception as e:
            return TransactionResult(
                signature=signature,
                status=TransactionStatus.FAILED,
                error=str(e),
            )

    async def close(self):
        """关闭所有连接"""
        if self._owns_clients:
            await self._rpc.close()
        await self._jupiter.close()
        await self._raydium.close()
