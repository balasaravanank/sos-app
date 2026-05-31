from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
from app.services.cache_service import get_emergency_contacts

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

@router.get("/emergency-contacts")
async def handle_get_emergency_contacts(request: Request):
    try:
        contacts = await get_emergency_contacts()
        return wrap_response(request, data={"contacts": contacts})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
