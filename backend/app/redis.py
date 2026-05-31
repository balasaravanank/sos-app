"""Upstash Redis client — class-based wrapper using httpx.

Supports Upstash REST API (HTTP) and falls back to an in-memory MockRedis
when credentials are not configured. All calls are failure-safe — if Redis
is down we log and degrade gracefully.
"""

import os
import json
import logging
import httpx
from typing import Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")


# ---------------------------------------------------------------------------
# In-memory fallback
# ---------------------------------------------------------------------------

class MockRedis:
    """In-memory Redis stand-in for local dev / offline mode."""

    def __init__(self):
        self.store: dict[str, Any] = {}
        logger.warning("Using in-memory MockRedis fallback.")

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.store[key] = value
        return True

    async def delete(self, key: str) -> bool:
        self.store.pop(key, None)
        return True

    async def incr(self, key: str) -> int:
        if key not in self.store:
            self.store[key] = "0"
        self.store[key] = str(int(self.store[key]) + 1)
        return int(self.store[key])

    async def expire(self, key: str, seconds: int) -> bool:
        return True  # Mock doesn't implement TTL


# ---------------------------------------------------------------------------
# Upstash HTTP client
# ---------------------------------------------------------------------------

class UpstashRedis:
    """Upstash Redis REST API client."""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    async def _execute(self, command: str, *args) -> Any:
        try:
            async with httpx.AsyncClient() as client:
                body = [command] + [str(a) for a in args]
                response = await client.post(
                    self.url, headers=self.headers, json=body, timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        logger.error("Upstash Redis Error: %s", data["error"])
                        return None
                    return data.get("result")
                else:
                    logger.error("Upstash Redis HTTP Error: %s", response.status_code)
                    return None
        except Exception as e:
            logger.warning("Redis operation failed: %s", e)
            return None

    async def get(self, key: str) -> str | None:
        return await self._execute("GET", key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        if ex is not None:
            result = await self._execute("SET", key, value, "EX", ex)
        else:
            result = await self._execute("SET", key, value)
        return result is not None

    async def delete(self, key: str) -> bool:
        result = await self._execute("DEL", key)
        return result is not None

    async def incr(self, key: str) -> int:
        result = await self._execute("INCR", key)
        return int(result) if result is not None else 0

    async def expire(self, key: str, seconds: int) -> bool:
        result = await self._execute("EXPIRE", key, seconds)
        return result is not None


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_redis_client = None


def get_redis() -> MockRedis | UpstashRedis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        if UPSTASH_URL and UPSTASH_TOKEN:
            _redis_client = UpstashRedis(UPSTASH_URL, UPSTASH_TOKEN)
            logger.info("Redis: Upstash HTTP client configured")
        else:
            _redis_client = MockRedis()
    return _redis_client


# ---------------------------------------------------------------------------
# Convenience helpers (used by roadsos-services / nearby_lookup)
# ---------------------------------------------------------------------------

# In-memory fallback cache for sync-style cache_get / cache_set
_memory_cache: dict[str, tuple[str, float]] = {}


def cache_get(key: str) -> dict | None:
    """Sync-friendly cache get (in-memory with TTL). Used by services layer."""
    import time
    if key in _memory_cache:
        val_str, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            return json.loads(val_str)
        else:
            del _memory_cache[key]
    return None


def cache_set(key: str, value: dict | list, ttl_seconds: int = 21600) -> None:
    """Sync-friendly cache set (in-memory with TTL). Default 6 hours."""
    import time
    _memory_cache[key] = (json.dumps(value), time.time() + ttl_seconds)
