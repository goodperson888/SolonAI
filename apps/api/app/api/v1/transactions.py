"""
Solana transaction API.

Provides non-custodial transaction utilities:
- read on-chain transaction history
- broadcast already-signed transactions
- query transaction status
"""

import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Add services/ to import the blockchain package when running the API app.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

router = APIRouter()


def get_transaction_service():
    """Import lazily so optional blockchain deps do not break API startup."""
    try:
        from blockchain.services.transaction_service import TransactionService  # noqa: WPS433

        return TransactionService()
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"区块链交易服务依赖未安装。缺少: {missing_package}",
        ) from exc


class TransactionHistoryItem(BaseModel):
    """On-chain signature history item."""

    signature: str
    slot: int
    err: Optional[object] = None
    memo: Optional[str] = None
    block_time: Optional[int] = None
    block_time_iso: Optional[datetime] = None
    confirmation_status: Optional[str] = None


class BroadcastTransactionRequest(BaseModel):
    """Broadcast a wallet-signed transaction."""

    signed_tx_base64: str = Field(..., description="Base64 encoded signed transaction")


class SerializedTransactionRequest(BaseModel):
    """Serialized transaction payload."""

    transaction_base64: str = Field(..., description="Base64 encoded serialized transaction")


class BatchInstructionRequest(BaseModel):
    """Batch instruction packing request."""

    payer: str = Field(..., description="Fee payer public key")
    instructions: list[dict] = Field(default_factory=list, description="Instruction payloads")
    recent_blockhash: Optional[str] = Field(default=None, description="Optional recent blockhash")
    max_instructions_per_tx: int = Field(default=8, ge=1, le=32)
    max_tx_size_bytes: int = Field(default=1232, ge=256, le=1232)
    compute_unit_limit: Optional[int] = Field(default=None, ge=1)
    compute_unit_price_micro_lamports: Optional[int] = Field(default=None, ge=0)


class TransactionStatusResponse(BaseModel):
    """Transaction status response."""

    signature: str
    status: str
    slot: Optional[int] = None
    error: Optional[str] = None


@router.get("/history/{wallet_address}", response_model=list[TransactionHistoryItem])
async def get_transaction_history(
    wallet_address: str,
    limit: int = Query(default=20, ge=1, le=100),
    before: Optional[str] = None,
    until: Optional[str] = None,
):
    """Fetch on-chain transaction signature history for a wallet address."""
    service = get_transaction_service()
    try:
        history = await service.get_transaction_history(
            wallet_address=wallet_address,
            limit=limit,
            before=before,
            until=until,
        )
        return [
            TransactionHistoryItem(
                **item,
                block_time_iso=datetime.fromtimestamp(item["block_time"])
                if item.get("block_time")
                else None,
            )
            for item in history
        ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询链上交易历史失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/broadcast", response_model=TransactionStatusResponse)
async def broadcast_transaction(request: BroadcastTransactionRequest):
    """Broadcast an already-signed transaction to Solana RPC."""
    service = get_transaction_service()
    try:
        result = await service.send_signed_transaction(request.signed_tx_base64)
        return TransactionStatusResponse(
            signature=result.signature,
            status=result.status.value,
            slot=result.slot,
            error=result.error,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"广播交易失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/parse")
async def parse_transaction(request: SerializedTransactionRequest):
    """Parse transaction signatures, accounts, and instructions."""
    service = get_transaction_service()
    try:
        return await service.parse_transaction(request.transaction_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"解析交易失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/signatures/parse")
async def parse_transaction_signatures(request: SerializedTransactionRequest):
    """Parse only transaction signature information."""
    service = get_transaction_service()
    try:
        return await service.parse_transaction_signatures(request.transaction_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"解析签名失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/estimate")
async def estimate_transaction(request: SerializedTransactionRequest):
    """Estimate network fee and simulation cost for a transaction."""
    service = get_transaction_service()
    try:
        return await service.estimate_transaction_cost(request.transaction_base64)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"估算交易费用失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/batch/pack")
async def pack_batch_transactions(request: BatchInstructionRequest):
    """Pack multiple instructions into one or more unsigned v0 transactions."""
    if not request.instructions:
        raise HTTPException(status_code=400, detail="instructions 不能为空")

    service = get_transaction_service()
    try:
        return {
            "transactions": await service.pack_batch_transactions(
                instructions=request.instructions,
                payer=request.payer,
                recent_blockhash=request.recent_blockhash,
                max_instructions_per_tx=request.max_instructions_per_tx,
                max_tx_size_bytes=request.max_tx_size_bytes,
                compute_unit_limit=request.compute_unit_limit,
                compute_unit_price_micro_lamports=request.compute_unit_price_micro_lamports,
            )
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"批量打包交易失败: {exc}") from exc
    finally:
        await service.close()


@router.get("/{signature}/status", response_model=TransactionStatusResponse)
async def get_transaction_status(signature: str):
    """Query transaction status by signature."""
    service = get_transaction_service()
    try:
        result = await service.get_transaction_status(signature)
        return TransactionStatusResponse(
            signature=result.signature,
            status=result.status.value,
            slot=result.slot,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询交易状态失败: {exc}") from exc
    finally:
        await service.close()
