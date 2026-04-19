"""
交易构建工具
提供交易构建、序列化等功能
"""

from typing import Any, Dict, List

from solana.transaction import Transaction
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey


class TransactionBuilder:
    """交易构建器"""

    @staticmethod
    def build_transaction(
        instructions: List[Instruction], payer: Pubkey, recent_blockhash: str
    ) -> Transaction:
        """
        构建交易

        Args:
            instructions: 指令列表
            payer: 交易费用支付者
            recent_blockhash: 最近的区块哈希

        Returns:
            未签名的交易
        """
        tx = Transaction()
        tx.recent_blockhash = recent_blockhash
        tx.fee_payer = payer

        for instruction in instructions:
            tx.add(instruction)

        return tx

    @staticmethod
    def create_instruction(
        program_id: str, accounts: List[Dict[str, Any]], data: bytes
    ) -> Instruction:
        """
        创建指令

        Args:
            program_id: 程序ID
            accounts: 账户列表
            data: 指令数据

        Returns:
            指令对象
        """
        account_metas = [
            AccountMeta(
                pubkey=Pubkey.from_string(acc["pubkey"]),
                is_signer=acc.get("is_signer", False),
                is_writable=acc.get("is_writable", False),
            )
            for acc in accounts
        ]

        return Instruction(
            program_id=Pubkey.from_string(program_id), accounts=account_metas, data=data
        )

    @staticmethod
    def serialize_transaction(tx: Transaction) -> bytes:
        """
        序列化交易

        Args:
            tx: 交易对象

        Returns:
            序列化后的交易数据
        """
        return tx.serialize()
