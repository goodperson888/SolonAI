import json
import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Optional
from uuid import UUID

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return str(value)


async def cache_get_json(redis: Redis, key: str) -> Optional[Any]:
    try:
        cached = await redis.get(key)
        if not cached:
            return None
        return json.loads(cached)
    except Exception as exc:
        logger.warning("Redis cache get failed for key=%s: %s", key, exc)
        return None


async def cache_set_json(redis: Redis, key: str, value: Any, ttl: int) -> None:
    try:
        await redis.setex(key, ttl, json.dumps(value, default=_json_default, ensure_ascii=False))
    except Exception as exc:
        logger.warning("Redis cache set failed for key=%s: %s", key, exc)


async def cache_delete(redis: Redis, *keys: str) -> None:
    try:
        valid_keys = [key for key in keys if key]
        if valid_keys:
            await redis.delete(*valid_keys)
    except Exception as exc:
        logger.warning("Redis cache delete failed for keys=%s: %s", keys, exc)


async def cache_delete_by_patterns(redis: Redis, patterns: Iterable[str]) -> None:
    try:
        keys_to_delete = []
        for pattern in patterns:
            async for key in redis.scan_iter(match=pattern):
                keys_to_delete.append(key)
        if keys_to_delete:
            await redis.delete(*keys_to_delete)
    except Exception as exc:
        logger.warning("Redis cache delete by pattern failed for patterns=%s: %s", patterns, exc)
