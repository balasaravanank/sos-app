import json
import logging
from app.redis import get_redis

logger = logging.getLogger(__name__)

STATIC_CONTACTS = [
    {"name": "108 Ambulance", "phone": "108"},
    {"name": "100 Police", "phone": "100"},
    {"name": "112 Emergency", "phone": "112"},
    {"name": "101 Fire Service", "phone": "101"}
]

async def get_emergency_contacts() -> list:
    redis = get_redis()
    key = "emergency_contacts"
    try:
        cached_str = await redis.get(key)
        if cached_str:
            return json.loads(cached_str)
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        
    # Not in cache or Redis failed, use static list
    contacts = STATIC_CONTACTS
    
    # Try to cache it for next time
    try:
        await redis.set(key, json.dumps(contacts), ex=86400) # 24h
    except Exception as e:
        logger.error(f"Redis set failed: {e}")
        
    return contacts
