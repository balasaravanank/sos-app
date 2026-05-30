from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.db import get_db
from app.schemas.location import LocationUpdateRequest, LocationStopRequest
from app.services.location_service import update_location, stop_location_stream, get_cached_location

router = APIRouter()

def wrap_response(request: Request, data: dict = None, error: str = None):
    res = {
        "success": error is None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": getattr(request.state, "request_id", None)
        }
    }
    if data is not None:
        res["data"] = data
    if error is not None:
        res["error"] = error
    return res

@router.post("/update")
async def handle_update_location(
    request: Request,
    body: LocationUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        await update_location(db, body)
        return wrap_response(request, data={"recorded": True})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def handle_stop_location(
    request: Request,
    body: LocationStopRequest
):
    try:
        await stop_location_stream(body)
        return wrap_response(request, data={"stopped": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cached")
async def handle_get_cached_location(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await get_cached_location(db, user_id)
        if not data:
            raise HTTPException(status_code=404, detail="Location not found")
        return wrap_response(request, data=data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
