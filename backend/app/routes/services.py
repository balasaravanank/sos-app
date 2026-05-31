# Services related routes (F-07) — ROADSoS Nearest Services Lookup
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.services import VALID_SERVICE_TYPES
from app.services.nearby_lookup import find_nearby, get_service_by_id, get_offline_pack
from app.utils import build_success_response, build_error_response, now_iso, generate_request_id

router = APIRouter()


@router.get("/nearby")
async def nearby_services(
    lat: float = Query(None, ge=-90, le=90),
    lng: float = Query(None, ge=-180, le=180),
    type: str = Query("hospital"),
    radius: int = Query(5000, ge=500, le=50000),
    db: Session = Depends(get_db),
):
    """
    GET /api/services/nearby
    Returns nearest services by type, sorted by distance.
    Primary: Google Places API | Fallback: Local DB | Last resort: Hardcoded data
    """
    # Validate required params
    if lat is None or lng is None:
        return JSONResponse(
            status_code=400,
            content=build_error_response("LOCATION_MISSING", "lat and lng query parameters are required"),
        )

    # Validate service type
    if type not in VALID_SERVICE_TYPES:
        return JSONResponse(
            status_code=400,
            content=build_error_response(
                "INVALID_SERVICE_TYPE",
                f"Invalid type '{type}'. Must be one of: {', '.join(VALID_SERVICE_TYPES)}",
            ),
        )

    services, source = await find_nearby(lat, lng, type, radius, db)

    return build_success_response(
        data={"services": services},
        source=source,
        count=len(services),
    )


@router.get("/types")
async def service_types():
    """
    GET /api/services/types
    Returns all available service type filters.
    """
    return build_success_response(
        data={"types": VALID_SERVICE_TYPES},
    )


@router.get("/offline-pack")
async def offline_pack(
    lat: float = Query(None, ge=-90, le=90),
    lng: float = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    """
    GET /api/services/offline-pack
    Returns all P0 service types for the given location.
    Frontend stores this in localStorage for offline access.
    """
    if lat is None or lng is None:
        return JSONResponse(
            status_code=400,
            content=build_error_response("LOCATION_MISSING", "lat and lng query parameters are required"),
        )

    services, types_found = await get_offline_pack(lat, lng, db)

    return build_success_response(
        data={"services": services, "cached_at": now_iso()},
        types_included=types_found,
        total_count=len(services),
    )


@router.get("/{service_id}")
async def service_detail(
    service_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /api/services/{service_id}
    Returns detail for a single cached service by UUID.
    """
    service = get_service_by_id(db, service_id)

    if service is None:
        return JSONResponse(
            status_code=404,
            content=build_error_response("SERVICE_NOT_FOUND", f"No service found with id '{service_id}'"),
        )

    return build_success_response(data=service)
