"""
Lightweight DeFi data refresh scheduler.

Runs inside the API process and periodically warms the blockchain aggregation
cache. It intentionally avoids extra dependencies such as APScheduler/Celery
for the local development environment.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

_refresh_task: Optional[asyncio.Task] = None


async def _refresh_once() -> None:
    from blockchain.services.defi_aggregation_service import DeFiAggregationService

    service = DeFiAggregationService()
    try:
        result = await service.warm_cache()
        logger.info("DeFi aggregation cache refreshed: %s", result)
    finally:
        await service.close()


async def _refresh_loop(interval_seconds: int) -> None:
    while True:
        try:
            await _refresh_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("DeFi aggregation refresh failed: %s", exc)

        await asyncio.sleep(interval_seconds)


def start_defi_scheduler(interval_seconds: int = 120) -> None:
    """Start the background refresh loop if it is not already running."""
    global _refresh_task
    if _refresh_task and not _refresh_task.done():
        return
    _refresh_task = asyncio.create_task(_refresh_loop(interval_seconds))


async def stop_defi_scheduler() -> None:
    """Stop the background refresh loop."""
    global _refresh_task
    if not _refresh_task:
        return

    _refresh_task.cancel()
    try:
        await _refresh_task
    except asyncio.CancelledError:
        pass
    finally:
        _refresh_task = None
