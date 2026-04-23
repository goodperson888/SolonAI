"""
DeFi market data aggregation service.

Aggregates live token prices and protocol yield data into one cacheable
payload for API endpoints and AI agents.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..cache import cached, get_cache
from ..config import config
from ..providers.jupiter import JupiterProvider
from ..providers.marginfi import MarginFiProvider
from ..providers.raydium import RaydiumProvider

logger = logging.getLogger(__name__)


DEFAULT_PRICE_TOKENS = {
    "SOL": config.WRAPPED_SOL_MINT,
    "USDC": config.MAINNET_TOKENS["USDC"],
    "USDT": config.MAINNET_TOKENS["USDT"],
}

MIN_OPPORTUNITY_TVL_USD = Decimal("10000")


class DeFiAggregationService:
    """Aggregate prices, protocol APY data, cache state, and refreshes."""

    def __init__(
        self,
        jupiter: Optional[JupiterProvider] = None,
        raydium: Optional[RaydiumProvider] = None,
        marginfi: Optional[MarginFiProvider] = None,
    ):
        self._jupiter = jupiter or JupiterProvider()
        self._raydium = raydium or RaydiumProvider()
        self._marginfi = marginfi or MarginFiProvider()
        self._owns_jupiter = jupiter is None
        self._owns_raydium = raydium is None
        self._owns_marginfi = marginfi is None

    @cached("defi_aggregation_overview", ttl=config.CACHE_TTL_DEFI_RATES)
    async def get_overview(self) -> Dict[str, Any]:
        """Return a unified DeFi market snapshot."""
        prices, yields = await asyncio.gather(
            self.get_realtime_prices(),
            self.get_protocol_yields(),
        )
        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "prices": prices,
            "yields": yields,
            "cache": get_cache().stats,
        }

    @cached("defi_aggregation_prices", ttl=config.CACHE_TTL_TOKEN_PRICE)
    async def get_realtime_prices(
        self,
        tokens: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch real-time USD prices from Jupiter Price API."""
        token_map = tokens or DEFAULT_PRICE_TOKENS
        prices = await self._jupiter.batch_get_token_prices(list(token_map.values()))

        result: Dict[str, Dict[str, Any]] = {}
        for symbol, mint in token_map.items():
            price = prices.get(mint)
            result[symbol] = {
                "symbol": symbol,
                "mint": mint,
                "price_usd": float(price) if price is not None else None,
                "source": "jupiter",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        return result

    @cached("defi_aggregation_yields", ttl=config.CACHE_TTL_DEFI_RATES)
    async def get_protocol_yields(self) -> Dict[str, Any]:
        """Aggregate protocol APY/TVL data from supported providers."""
        marginfi_result, raydium_result = await asyncio.gather(
            self._get_marginfi_yields(),
            self._get_raydium_yields(),
            return_exceptions=True,
        )

        protocols: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        if isinstance(marginfi_result, Exception):
            errors["marginfi"] = str(marginfi_result)
        else:
            protocols["marginfi"] = marginfi_result

        if isinstance(raydium_result, Exception):
            errors["raydium"] = str(raydium_result)
        else:
            protocols["raydium"] = raydium_result

        opportunities = self._rank_opportunities(protocols)

        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "protocols": protocols,
            "best_opportunities": opportunities,
            "errors": errors,
        }

    async def warm_cache(self) -> Dict[str, Any]:
        """Refresh the main aggregation paths and return cache stats."""
        overview = await self.get_overview()
        return {
            "warmed": True,
            "updated_at": overview["updated_at"],
            "cache": get_cache().stats,
        }

    async def _get_marginfi_yields(self) -> Dict[str, Any]:
        pools = await self._marginfi.get_lending_pools()
        normalized = []
        for pool in pools:
            item = pool.to_dict()
            item["type"] = "lending"
            item["apy"] = item.get("deposit_apy", 0.0)
            item["tvl_usd"] = item.get("total_deposits", 0.0)
            normalized.append(item)

        return {
            "name": "MarginFi",
            "type": "lending",
            "source": "marginfi/defillama",
            "pools": normalized,
        }

    async def _get_raydium_yields(self) -> Dict[str, Any]:
        pools = await self._raydium.get_pool_list(page_size=25)
        normalized = []

        for pool in pools:
            mint_a = pool.get("mintA") or {}
            mint_b = pool.get("mintB") or {}
            day = pool.get("day") or {}
            week = pool.get("week") or {}
            month = pool.get("month") or {}
            symbol = f"{mint_a.get('symbol', '?')}-{mint_b.get('symbol', '?')}"
            apy = _first_decimal(day.get("apr"), week.get("apr"), month.get("apr"))
            tvl = _to_decimal(pool.get("tvl"))
            if tvl < MIN_OPPORTUNITY_TVL_USD:
                continue

            normalized.append(
                {
                    "protocol": "raydium",
                    "type": "liquidity_pool",
                    "symbol": symbol,
                    "pool_address": pool.get("id"),
                    "mint_a": mint_a.get("address"),
                    "mint_b": mint_b.get("address"),
                    "apy": float(apy),
                    "fee_apr": float(_first_decimal(day.get("feeApr"), week.get("feeApr"))),
                    "reward_apr": [
                        float(_to_decimal(value)) for value in (day.get("rewardApr") or [])
                    ],
                    "tvl_usd": float(tvl),
                    "volume_24h": float(_to_decimal(day.get("volume"))),
                    "source": "raydium",
                }
            )

        return {
            "name": "Raydium",
            "type": "dex",
            "source": "raydium",
            "pools": normalized,
        }

    @staticmethod
    def _rank_opportunities(protocols: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        opportunities = []
        for protocol, data in protocols.items():
            for pool in data.get("pools", []):
                apy = _to_decimal(pool.get("apy") or pool.get("deposit_apy"))
                if apy <= 0:
                    continue
                tvl = _to_decimal(pool.get("tvl_usd") or pool.get("total_deposits"))
                if tvl < MIN_OPPORTUNITY_TVL_USD:
                    continue
                opportunities.append(
                    {
                        "protocol": protocol,
                        "symbol": pool.get("symbol"),
                        "type": pool.get("type"),
                        "apy": float(apy),
                        "tvl_usd": float(tvl),
                    }
                )
        return sorted(opportunities, key=lambda item: item["apy"], reverse=True)[:limit]

    async def close(self):
        """Close owned provider clients."""
        if self._owns_jupiter:
            await self._jupiter.close()
        if self._owns_raydium:
            await self._raydium.close()
        if self._owns_marginfi:
            await self._marginfi.close()


def _to_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _first_decimal(*values: Any) -> Decimal:
    for value in values:
        decimal_value = _to_decimal(value)
        if decimal_value > 0:
            return decimal_value
    return Decimal("0")
