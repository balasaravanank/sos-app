import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException
from geoalchemy2.elements import WKTElement
from app.models.location import LocationHistory
from app.schemas.location import LocationUpdateRequest, LocationStopRequest
from app.redis import get_redis

logger = logging.getLogger(__name__)

async def check_rate_limit(user_id: UUID) -> bool:
    redis = get_redis()
    key = f"rate:user:{user_id}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        return count <= 60
    except Exception as e:
        logger.error(f"Redis rate limit check failed: {e}")
        return True # Graceful bypass

async def update_location(db: AsyncSession, payload: LocationUpdateRequest) -> bool:
    # 1. Rate Limit Check
    is_allowed = await check_rate_limit(payload.user_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="RATE_LIMITED")

    # 2. Save to PostgreSQL
    new_loc = LocationHistory(
        user_id=payload.user_id,
        sos_id=payload.sos_id,
        latitude=payload.lat,
        longitude=payload.lng,
        accuracy=payload.accuracy,
        geom=WKTElement(f'POINT({payload.lng} {payload.lat})', srid=4326)
    )
    
    db.add(new_loc)
    await db.commit()

    # 3. Update Redis cache
    redis = get_redis()
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        cached_data = json.dumps({
            "lat": payload.lat,
            "lng": payload.lng,
            "accuracy": payload.accuracy,
            "cached_at": now_str
        })
        await redis.set(f"location:user:{payload.user_id}", cached_data, ex=86400) # 24h
        
        if payload.sos_id:
            live_data = json.dumps({
                "user_id": str(payload.user_id),
                "lat": payload.lat,
                "lng": payload.lng,
                "updated_at": now_str
            })
            await redis.set(f"sos:live:{payload.sos_id}", live_data, ex=3600) # 60min
    except Exception as e:
        logger.error(f"Redis update failed: {e}")
        
    return True

async def stop_location_stream(payload: LocationStopRequest) -> bool:
    redis = get_redis()
    try:
        await redis.delete(f"sos:live:{payload.sos_id}")
        logger.info(f"Stream stopped for sos_id {payload.sos_id}")
    except Exception as e:
        logger.error(f"Redis delete failed: {e}")
    return True

async def get_cached_location(db: AsyncSession, user_id: UUID) -> dict:
    redis = get_redis()
    try:
        cached_str = await redis.get(f"location:user:{user_id}")
        if cached_str:
            return json.loads(cached_str)
    except Exception as e:
        logger.error(f"Redis get failed: {e}")
        
    # Fallback to DB
    result = await db.execute(
        select(LocationHistory)
        .where(LocationHistory.user_id == user_id)
        .order_by(desc(LocationHistory.created_at))
        .limit(1)
    )
    loc = result.scalars().first()
    
    if not loc:
        return None
        
    return {
        "lat": loc.latitude,
        "lng": loc.longitude,
        "cached_at": loc.created_at.isoformat()
    }
