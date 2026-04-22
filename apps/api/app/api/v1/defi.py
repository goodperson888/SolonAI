"""
DeFi market data API.

Exposes aggregated protocol APY, real-time prices, cache stats, and a manual
refresh hook used by the lightweight background scheduler.
"""

import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

router = APIRouter()


def get_defi_service():
    """Import lazily so optional blockchain deps do not break API startup."""
    try:
        from blockchain.cache import get_cache  # noqa: WPS433
        from blockchain.config import config  # noqa: WPS433
        from blockchain.services.defi_aggregation_service import (  # noqa: WPS433
            DeFiAggregationService,
        )

        return DeFiAggregationService(), get_cache, config
    except ModuleNotFoundError as exc:
        missing_package = exc.name or "unknown dependency"
        raise HTTPException(
            status_code=503,
            detail=f"DeFi 聚合服务依赖未安装。缺少: {missing_package}",
        ) from exc


@router.get("/overview")
async def get_defi_overview():
    """Get aggregated prices, APY/TVL, and cache stats."""
    service, _, _ = get_defi_service()
    try:
        return await service.get_overview()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取 DeFi 聚合数据失败: {exc}") from exc
    finally:
        await service.close()


@router.get("/prices")
async def get_realtime_prices(
    symbols: Optional[str] = Query(
        default=None,
        description="逗号分隔的符号列表，当前支持 SOL,USDC,USDT",
    ),
):
    """Get real-time token prices from Jupiter."""
    service, _, config = get_defi_service()
    token_map = None
    if symbols:
        supported = {
            "SOL": config.WRAPPED_SOL_MINT,
            "USDC": config.MAINNET_TOKENS["USDC"],
            "USDT": config.MAINNET_TOKENS["USDT"],
        }
        requested = [symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()]
        token_map = {symbol: supported[symbol] for symbol in requested if symbol in supported}
        if not token_map:
            raise HTTPException(status_code=400, detail="没有可支持的价格符号")

    try:
        return await service.get_realtime_prices(token_map)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取实时价格失败: {exc}") from exc
    finally:
        await service.close()


@router.get("/yields")
async def get_protocol_yields():
    """Get aggregated protocol APY/TVL data."""
    service, _, _ = get_defi_service()
    try:
        return await service.get_protocol_yields()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取协议 APY 失败: {exc}") from exc
    finally:
        await service.close()


@router.post("/refresh")
async def refresh_defi_cache():
    """Manually warm the DeFi aggregation cache."""
    service, _, _ = get_defi_service()
    try:
        return await service.warm_cache()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"刷新 DeFi 缓存失败: {exc}") from exc
    finally:
        await service.close()


@router.get("/cache/stats")
async def get_defi_cache_stats():
    """Return blockchain aggregation cache stats."""
    _, get_cache, _ = get_defi_service()
    return get_cache().stats
