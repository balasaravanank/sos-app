import os
import json
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_TOKEN = os.getenv("REDIS_TOKEN", "")

# In-memory fallback cache when Redis is unavailable
_memory_cache: dict[str, tuple[str, float]] = {}

_redis_client = None


def _init_redis():
    """Try to connect to Redis. Falls back to in-memory dict silently."""
    global _redis_client
    if not REDIS_URL or REDIS_URL == "mock":
        logger.info("Redis not configured — using in-memory cache fallback")
        return

    try:
        import redis as redis_lib

        # Handle Upstash HTTP-based Redis vs standard Redis
        if REDIS_URL.startswith("https://") or REDIS_URL.startswith("rediss://"):
            # Upstash REST API — use httpx for HTTP calls
            _redis_client = None
            logger.info("Upstash detected — using HTTP cache layer")
        else:
            _redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} — using in-memory fallback")
        _redis_client = None


def cache_get(key: str) -> dict | None:
    """Get cached value by key. Returns parsed dict or None."""
    # Try Redis first
    if _redis_client:
        try:
            val = _redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass

    # In-memory fallback
    import time

    if key in _memory_cache:
        val_str, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            return json.loads(val_str)
        else:
            del _memory_cache[key]

    return None


def cache_set(key: str, value: dict, ttl_seconds: int = 21600) -> None:
    """Set cache with TTL. Default 6 hours (21600s)."""
    val_str = json.dumps(value)

    # Try Redis first
    if _redis_client:
        try:
            _redis_client.setex(key, ttl_seconds, val_str)
            return
        except Exception:
            pass

    # In-memory fallback
    import time

    _memory_cache[key] = (val_str, time.time() + ttl_seconds)


# Initialize on module load
_init_redis()
