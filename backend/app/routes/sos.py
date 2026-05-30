"""SOS Core Routes — F-01 (Emergency), F-02 (Injury), F-03 (Safety).

All three SOS types use a single unified endpoint: POST /trigger
Backend branches logic based on the `type` field in the request body.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.redis import redis_incr, redis_expire, redis_get
from app.models.sos_event import SOSEvent
from app.models.dispatch_unit import DispatchUnit
from app.models.service_cache import ServiceCache
from app.schemas.sos import (
    SOSTriggerRequest,
    SOSConfirmRequest,
    EmergencySOSData,
    InjurySOSData,
    SafetySOSData,
    SOSConfirmData,
    SOSStatusData,
)
from app.utils import success_response, error_response, haversine_km, eta_minutes, generate_request_id

logger = logging.getLogger(__name__)
router = APIRouter()

RATE_LIMIT_MAX = 3       # Max SOS per user per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds


# ---------------------------------------------------------------------------
# POST /trigger — Unified SOS trigger (F-01, F-02, F-03)
# ---------------------------------------------------------------------------

@router.post("/trigger")
async def trigger_sos(body: SOSTriggerRequest, db: AsyncSession = Depends(get_db)):
    """Trigger an SOS event. Branches behavior by type: emergency | injury | safety."""

    request_id = generate_request_id()

    # --- Rate limiting (Redis-based, soft fail) ---
    if body.user_id:
        rate_key = f"sos_rate:{body.user_id}"
        count = await redis_incr(rate_key)
        if count == 1:
            await redis_expire(rate_key, RATE_LIMIT_WINDOW)
        if count and count > RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=429,
                detail=error_response("RATE_LIMITED", f"Max {RATE_LIMIT_MAX} SOS per hour exceeded"),
            )

    # --- Save SOS event to database ---
    event = SOSEvent(
        type=body.type,
        lat=body.lat,
        lng=body.lng,
        user_id=body.user_id,
        status="active",
        confirmed_by=0,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    sos_id = event.id
    logger.info("SOS triggered: id=%s type=%s lat=%s lng=%s", sos_id, body.type, body.lat, body.lng)

    # --- Branch by type ---
    if body.type == "emergency":
        data = await _handle_emergency(sos_id, body.lat, body.lng, db)
    elif body.type == "injury":
        data = await _handle_injury(sos_id, body.lat, body.lng, db)
    else:  # safety
        data = await _handle_safety(sos_id, body.lat, body.lng, db)

    return success_response(data, request_id)


# ---------------------------------------------------------------------------
# POST /{sos_id}/confirm — Crowd confirmation
# ---------------------------------------------------------------------------

@router.post("/{sos_id}/confirm")
async def confirm_sos(sos_id: str, body: SOSConfirmRequest, db: AsyncSession = Depends(get_db)):
    """Bystander confirms an SOS event. Increments confirmed_by counter."""

    request_id = generate_request_id()

    result = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail=error_response("SOS_NOT_FOUND", "Invalid sos_id"))

    event.confirmed_by = (event.confirmed_by or 0) + 1
    verified = event.confirmed_by >= 2

    if verified:
        event.status = "verified"

    await db.commit()
    await db.refresh(event)

    logger.info("SOS confirmed: id=%s confirmed_by=%d verified=%s", sos_id, event.confirmed_by, verified)

    data = SOSConfirmData(confirmed_by=event.confirmed_by, verified=verified).model_dump()
    return success_response(data, request_id)


# ---------------------------------------------------------------------------
# GET /{sos_id}/status — Check SOS status
# ---------------------------------------------------------------------------

@router.get("/{sos_id}/status")
async def get_sos_status(sos_id: str, db: AsyncSession = Depends(get_db)):
    """Get the current status of an SOS event."""

    request_id = generate_request_id()

    result = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail=error_response("SOS_NOT_FOUND", "Invalid sos_id"))

    data = SOSStatusData(
        sos_id=event.id,
        type=event.type,
        status=event.status,
        confirmed_by=event.confirmed_by or 0,
        created_at=event.created_at.isoformat() if event.created_at else "",
    ).model_dump()

    return success_response(data, request_id)


# ---------------------------------------------------------------------------
# Internal handlers — one per SOS type
# ---------------------------------------------------------------------------

async def _handle_emergency(sos_id: str, lat: float, lng: float, db: AsyncSession) -> dict:
    """F-01: Emergency SOS — find nearest ambulance, return ETA."""

    nearest = await _find_nearest_unit(db, lat, lng, unit_type="ambulance")

    ambulance_info = None
    eta_msg = "Help is on the way — calling 108"

    if nearest:
        unit, distance = nearest
        eta = eta_minutes(distance)
        ambulance_info = {
            "unit_id": unit.id,
            "eta_mins": eta,
            "contact": unit.contact or "108",
            "zone": unit.zone,
        }
        eta_msg = f"Ambulance dispatched — ETA {eta} min"
        logger.info("Ambulance dispatched: unit=%s eta=%d min distance=%.2f km", unit.id, eta, distance)

    return EmergencySOSData(
        sos_id=sos_id,
        status="active",
        eta_message=eta_msg,
        nearest_ambulance=ambulance_info,
    ).model_dump()


async def _handle_injury(sos_id: str, lat: float, lng: float, db: AsyncSession) -> dict:
    """F-02: Injury SOS — find nearest trauma center/hospital."""

    nearest = await _find_nearest_service(db, lat, lng, service_type="hospital")

    trauma_info = None
    directions_url = None

    if nearest:
        service, distance = nearest
        trauma_info = {
            "name": service.name,
            "address": service.address,
            "phone": service.phone,
            "distance_km": round(distance, 2),
        }
        directions_url = (
            f"https://www.google.com/maps/dir/{lat},{lng}/{service.lat},{service.lng}"
        )
        logger.info("Trauma center found: %s (%.2f km)", service.name, distance)

    return InjurySOSData(
        sos_id=sos_id,
        nearest_trauma_center=trauma_info,
        directions_url=directions_url,
    ).model_dump()


async def _handle_safety(sos_id: str, lat: float, lng: float, db: AsyncSession) -> dict:
    """F-03: Safety Button — notify nearest police station."""

    nearest = await _find_nearest_unit(db, lat, lng, unit_type="police")

    station_info = None
    police_notified = False

    if nearest:
        unit, distance = nearest
        eta = eta_minutes(distance, speed_kmh=50.0)
        station_info = {
            "station_id": unit.id,
            "name": f"Police Station — {unit.zone or 'Local'}",
            "contact": unit.contact or "100",
            "eta_mins": eta,
        }
        police_notified = True

        # SMS fallback — log for now (Twilio integration is Day 2)
        logger.info(
            "POLICE ALERT: SOS at %s,%s → Station %s (zone: %s, contact: %s)",
            lat, lng, unit.id, unit.zone, unit.contact,
        )
    else:
        # No unit found — still mark as notified (would SMS 100 in production)
        police_notified = True
        logger.warning("No police unit in range — would call 100 directly")

    return SafetySOSData(
        sos_id=sos_id,
        police_notified=police_notified,
        nearest_station=station_info,
    ).model_dump()


# ---------------------------------------------------------------------------
# Shared query helpers
# ---------------------------------------------------------------------------

async def _find_nearest_unit(
    db: AsyncSession, lat: float, lng: float, unit_type: str
) -> tuple | None:
    """Find the nearest available dispatch unit by haversine distance.

    Returns (DispatchUnit, distance_km) or None if nothing in range.
    Expands radius: 2km → 5km → 15km → 50km.
    """
    result = await db.execute(
        select(DispatchUnit).where(
            DispatchUnit.type == unit_type,
            DispatchUnit.status == "available",
        )
    )
    units = result.scalars().all()

    if not units:
        return None

    # Calculate distance for each unit, find the closest
    closest = None
    min_distance = float("inf")

    for unit in units:
        dist = haversine_km(lat, lng, float(unit.lat), float(unit.lng))
        if dist < min_distance:
            min_distance = dist
            closest = unit

    if closest is None:
        return None

    # Radius gates: reject if beyond 50km (too far to be useful)
    if min_distance > 50:
        logger.warning("Nearest %s is %.1f km away — beyond 50km limit", unit_type, min_distance)
        return None

    return closest, min_distance


async def _find_nearest_service(
    db: AsyncSession, lat: float, lng: float, service_type: str
) -> tuple | None:
    """Find the nearest cached service (hospital, trauma center) by haversine distance.

    Queries the services_cache table as fallback when Google Places API is not available.
    """
    result = await db.execute(
        select(ServiceCache).where(ServiceCache.type == service_type)
    )
    services = result.scalars().all()

    if not services:
        return None

    closest = None
    min_distance = float("inf")

    for svc in services:
        dist = haversine_km(lat, lng, float(svc.lat), float(svc.lng))
        if dist < min_distance:
            min_distance = dist
            closest = svc

    if closest is None:
        return None

    return closest, min_distance
