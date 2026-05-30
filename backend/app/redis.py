import os
from dotenv import load_dotenv
import httpx
import logging
from typing import Optional, Dict, Any

load_dotenv()

logger = logging.getLogger(__name__)

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

class MockRedis:
    def __init__(self):
        self.store: Dict[str, Any] = {}
        logger.warning("Using in-memory MockRedis fallback.")
        
    async def get(self, key: str) -> Optional[str]:
        return self.store.get(key)
        
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self.store[key] = value
        return True
        
    async def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
        return True
        
    async def incr(self, key: str) -> int:
        if key not in self.store:
            self.store[key] = "0"
        self.store[key] = str(int(self.store[key]) + 1)
        return int(self.store[key])
        
    async def expire(self, key: str, seconds: int) -> bool:
        return True # Mock doesn't implement TTL expiration logic

class UpstashRedis:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {"Authorization": f"Bearer {token}"}
        
    async def _execute(self, command: str, *args) -> Any:
        try:
            async with httpx.AsyncClient() as client:
                body = [command] + list(args)
                response = await client.post(self.url, headers=self.headers, json=body, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        logger.error(f"Upstash Redis Error: {data['error']}")
                        raise Exception(data["error"])
                    return data.get("result")
                else:
                    logger.error(f"Upstash Redis HTTP Error: {response.status_code}")
                    raise Exception(f"HTTP Error {response.status_code}")
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise e

    async def get(self, key: str) -> Optional[str]:
        return await self._execute("GET", key)
        
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if ex is not None:
            res = await self._execute("SET", key, value, "EX", ex)
        else:
            res = await self._execute("SET", key, value)
        return res == "OK"
        
    async def delete(self, key: str) -> bool:
        res = await self._execute("DEL", key)
        return int(res or 0) > 0
        
    async def incr(self, key: str) -> int:
        res = await self._execute("INCR", key)
        return int(res or 0)
        
    async def expire(self, key: str, seconds: int) -> bool:
        res = await self._execute("EXPIRE", key, seconds)
        return int(res or 0) > 0

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        if UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN:
            _redis_client = UpstashRedis(UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN)
        else:
            _redis_client = MockRedis()
    return _redis_client
