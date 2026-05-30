"""Upstash Redis HTTP client — lightweight wrapper using httpx.

Upstash uses a REST API, not the standard Redis TCP protocol.
All calls are fire-and-forget safe — if Redis is down, we log and return None.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

_headers = {"Authorization": f"Bearer {UPSTASH_TOKEN}"} if UPSTASH_TOKEN else {}


async def _request(command: list[str]) -> dict | None:
    """Send a Redis command via Upstash REST API."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        logger.warning("Redis not configured — skipping command: %s", command[0])
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                UPSTASH_URL,
                headers=_headers,
                json=command,
                timeout=3.0,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Redis call failed (%s): %s", command[0], exc)
        return None


async def redis_get(key: str) -> str | None:
    """GET a key. Returns the value string or None."""
    result = await _request(["GET", key])
    return result.get("result") if result else None


async def redis_set(key: str, value: str, ex: int | None = None) -> bool:
    """SET a key with optional TTL in seconds."""
    cmd = ["SET", key, value]
    if ex:
        cmd.extend(["EX", str(ex)])
    result = await _request(cmd)
    return result is not None


async def redis_incr(key: str) -> int | None:
    """INCR a key. Returns the new integer value or None."""
    result = await _request(["INCR", key])
    return int(result["result"]) if result and result.get("result") is not None else None


async def redis_expire(key: str, seconds: int) -> bool:
    """Set TTL on an existing key."""
    result = await _request(["EXPIRE", key, str(seconds)])
    return result is not None
