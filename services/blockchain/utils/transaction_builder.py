"""
Solana transaction build utilities.

Provides helpers for:
- parsing serialized transactions and signatures
- estimating message shape before fee simulation
- packing multiple instructions into signable v0 transactions
"""

import base64
from dataclasses import dataclass
from typing import Any

from solana.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.message import Message, MessageV0
from solders.null_signer import NullSigner
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

MAX_SOLANA_TX_SIZE_BYTES = 1232


@dataclass(frozen=True)
class PackedTransaction:
    """A signable transaction produced by batch packing."""

    transaction_base64: str
    transaction_index: int
    instruction_count: int
    size_bytes: int
    required_signatures: int
    recent_blockhash: str


class TransactionBuilder:
    """Transaction builder and parser."""

    @staticmethod
    def build_transaction(
        instructions: list[Instruction],
        payer: Pubkey,
        recent_blockhash: str,
    ) -> Transaction:
        """
        Build a legacy transaction.

        This method is kept for compatibility with older code paths. New code
        should prefer `build_v0_transaction_base64`.
        """
        tx = Transaction()
        tx.recent_blockhash = recent_blockhash
        tx.fee_payer = payer

        for instruction in instructions:
            tx.add(instruction)

        return tx

    @staticmethod
    def create_instruction(
        program_id: str,
        accounts: list[dict[str, Any]],
        data: bytes,
    ) -> Instruction:
        """Create a solders instruction from a JSON-friendly payload."""
        account_metas = [
            AccountMeta(
                pubkey=Pubkey.from_string(acc["pubkey"]),
                is_signer=acc.get("is_signer", False),
                is_writable=acc.get("is_writable", False),
            )
            for acc in accounts
        ]

        return Instruction(
            program_id=Pubkey.from_string(program_id),
            accounts=account_metas,
            data=data,
        )

    @staticmethod
    def create_transfer_instruction(
        from_pubkey: str,
        to_pubkey: str,
        lamports: int,
    ) -> Instruction:
        """Create a native SOL transfer instruction."""
        return transfer(
            TransferParams(
                from_pubkey=Pubkey.from_string(from_pubkey),
                to_pubkey=Pubkey.from_string(to_pubkey),
                lamports=lamports,
            )
        )

    @staticmethod
    def serialize_transaction(tx: Transaction) -> bytes:
        """Serialize a legacy transaction."""
        return tx.serialize()

    @staticmethod
    def decode_transaction(transaction_base64: str) -> VersionedTransaction:
        """Decode a base64 serialized transaction into a VersionedTransaction."""
        try:
            raw = base64.b64decode(transaction_base64, validate=True)
            return VersionedTransaction.from_bytes(raw)
        except Exception as exc:
            raise ValueError(f"无法解析交易 base64: {exc}") from exc

    @staticmethod
    def encode_transaction(tx: VersionedTransaction) -> str:
        """Encode a VersionedTransaction as base64."""
        return base64.b64encode(bytes(tx)).decode("utf-8")

    @classmethod
    def parse_transaction(cls, transaction_base64: str) -> dict[str, Any]:
        """Parse transaction signatures, account keys, and instructions."""
        tx = cls.decode_transaction(transaction_base64)
        message = tx.message
        account_keys = list(message.account_keys)
        header = message.header
        signatures = [str(sig) for sig in tx.signatures]
        verify_results = [bool(result) for result in tx.verify_with_results()]
        required_signatures = int(header.num_required_signatures)

        return {
            "version": str(tx.version()),
            "size_bytes": len(bytes(tx)),
            "recent_blockhash": str(message.recent_blockhash),
            "required_signatures": required_signatures,
            "signature_count": len(signatures),
            "signed": bool(verify_results) and all(verify_results),
            "signatures": [
                {
                    "index": index,
                    "signature": signature,
                    "valid": verify_results[index] if index < len(verify_results) else False,
                    "signer": str(account_keys[index])
                    if index < required_signatures and index < len(account_keys)
                    else None,
                }
                for index, signature in enumerate(signatures)
            ],
            "accounts": cls._parse_accounts(message),
            "instructions": cls._parse_instructions(message),
            "address_table_lookup_count": len(getattr(message, "address_table_lookups", []) or []),
        }

    @classmethod
    def parse_signatures(cls, transaction_base64: str) -> dict[str, Any]:
        """Parse only the signature section from a serialized transaction."""
        parsed = cls.parse_transaction(transaction_base64)
        return {
            "required_signatures": parsed["required_signatures"],
            "signature_count": parsed["signature_count"],
            "signed": parsed["signed"],
            "signatures": parsed["signatures"],
        }

    @classmethod
    def build_v0_transaction_base64(
        cls,
        instructions: list[Instruction],
        payer: str,
        recent_blockhash: str,
        compute_unit_limit: int | None = None,
        compute_unit_price_micro_lamports: int | None = None,
    ) -> str:
        """Build an unsigned/signable v0 transaction encoded as base64."""
        payer_pubkey = Pubkey.from_string(payer)
        tx = cls._build_unsigned_v0_transaction(
            instructions=cls._with_compute_budget(
                instructions,
                compute_unit_limit,
                compute_unit_price_micro_lamports,
            ),
            payer=payer_pubkey,
            recent_blockhash=recent_blockhash,
        )
        return cls.encode_transaction(tx)

    @classmethod
    def pack_instructions(
        cls,
        instructions: list[Instruction],
        payer: str,
        recent_blockhash: str,
        max_instructions_per_tx: int = 8,
        max_tx_size_bytes: int = MAX_SOLANA_TX_SIZE_BYTES,
        compute_unit_limit: int | None = None,
        compute_unit_price_micro_lamports: int | None = None,
    ) -> list[PackedTransaction]:
        """
        Pack instructions into one or more unsigned v0 transactions.

        The packer keeps instruction order and starts a new transaction when
        either the instruction count or serialized size limit would be exceeded.
        """
        if not instructions:
            return []

        payer_pubkey = Pubkey.from_string(payer)
        packed: list[PackedTransaction] = []
        current: list[Instruction] = []

        def finalize(chunk: list[Instruction]) -> None:
            all_instructions = cls._with_compute_budget(
                chunk,
                compute_unit_limit,
                compute_unit_price_micro_lamports,
            )
            tx = cls._build_unsigned_v0_transaction(
                all_instructions,
                payer_pubkey,
                recent_blockhash,
            )
            packed.append(
                PackedTransaction(
                    transaction_base64=cls.encode_transaction(tx),
                    transaction_index=len(packed),
                    instruction_count=len(chunk),
                    size_bytes=len(bytes(tx)),
                    required_signatures=int(tx.message.header.num_required_signatures),
                    recent_blockhash=recent_blockhash,
                )
            )

        for instruction in instructions:
            candidate = [*current, instruction]
            if len(candidate) > max_instructions_per_tx:
                finalize(current)
                current = [instruction]
                continue

            candidate_tx = cls._build_unsigned_v0_transaction(
                cls._with_compute_budget(
                    candidate,
                    compute_unit_limit,
                    compute_unit_price_micro_lamports,
                ),
                payer_pubkey,
                recent_blockhash,
            )
            if len(bytes(candidate_tx)) > max_tx_size_bytes:
                if not current:
                    raise ValueError("单条指令超过交易大小限制，无法打包")
                finalize(current)
                current = [instruction]
            else:
                current = candidate

        if current:
            finalize(current)

        return packed

    @classmethod
    def instruction_from_payload(cls, payload: dict[str, Any]) -> Instruction:
        """Build an instruction from API payload data."""
        instruction_type = payload.get("type", "custom")
        if instruction_type == "system_transfer":
            return cls.create_transfer_instruction(
                from_pubkey=payload["from_pubkey"],
                to_pubkey=payload["to_pubkey"],
                lamports=int(payload["lamports"]),
            )

        data = payload.get("data", "")
        encoding = payload.get("encoding", "base64")
        if encoding == "base64":
            data_bytes = base64.b64decode(data or "", validate=True)
        elif encoding == "hex":
            data_bytes = bytes.fromhex(data or "")
        else:
            raise ValueError("encoding 仅支持 base64 或 hex")

        return cls.create_instruction(
            program_id=payload["program_id"],
            accounts=payload.get("accounts", []),
            data=data_bytes,
        )

    @classmethod
    def _build_unsigned_v0_transaction(
        cls,
        instructions: list[Instruction],
        payer: Pubkey,
        recent_blockhash: str,
    ) -> VersionedTransaction:
        message = MessageV0.try_compile(
            payer,
            instructions,
            [],
            Hash.from_string(recent_blockhash),
        )
        signers = [
            NullSigner(message.account_keys[index])
            for index in range(message.header.num_required_signatures)
        ]
        return VersionedTransaction(message, signers)

    @staticmethod
    def _with_compute_budget(
        instructions: list[Instruction],
        compute_unit_limit: int | None,
        compute_unit_price_micro_lamports: int | None,
    ) -> list[Instruction]:
        budget_instructions: list[Instruction] = []
        if compute_unit_limit is not None:
            budget_instructions.append(set_compute_unit_limit(int(compute_unit_limit)))
        if compute_unit_price_micro_lamports is not None:
            budget_instructions.append(
                set_compute_unit_price(int(compute_unit_price_micro_lamports))
            )
        return [*budget_instructions, *instructions]

    @classmethod
    def _parse_accounts(cls, message: Message | MessageV0) -> list[dict[str, Any]]:
        account_keys = list(message.account_keys)
        header = message.header
        required = int(header.num_required_signatures)
        readonly_signed_start = required - int(header.num_readonly_signed_accounts)
        readonly_unsigned_start = len(account_keys) - int(header.num_readonly_unsigned_accounts)

        accounts = []
        for index, key in enumerate(account_keys):
            is_signer = index < required
            if is_signer:
                is_writable = index < readonly_signed_start
            else:
                is_writable = index < readonly_unsigned_start

            accounts.append(
                {
                    "index": index,
                    "pubkey": str(key),
                    "is_signer": is_signer,
                    "is_writable": is_writable,
                }
            )
        return accounts

    @classmethod
    def _parse_instructions(cls, message: Message | MessageV0) -> list[dict[str, Any]]:
        account_keys = list(message.account_keys)
        instructions = []

        for index, instruction in enumerate(message.instructions):
            program_index = int(instruction.program_id_index)
            account_indexes = list(instruction.accounts)
            instructions.append(
                {
                    "index": index,
                    "program_id_index": program_index,
                    "program_id": cls._account_key_at(account_keys, program_index),
                    "account_indexes": [int(account_index) for account_index in account_indexes],
                    "accounts": [
                        cls._account_key_at(account_keys, int(account_index))
                        for account_index in account_indexes
                    ],
                    "data_base64": base64.b64encode(bytes(instruction.data)).decode("utf-8"),
                }
            )

        return instructions

    @staticmethod
    def _account_key_at(account_keys: list[Pubkey], index: int) -> str | None:
        if 0 <= index < len(account_keys):
            return str(account_keys[index])
        return None
