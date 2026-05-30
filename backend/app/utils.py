import math
import uuid
from datetime import datetime, timezone


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def eta_minutes(distance_km: float, speed_kmh: float = 40) -> int:
    """Estimate arrival time in minutes. Default 40 km/h for urban ambulance."""
    if speed_kmh <= 0:
        return 0
    return round((distance_km / speed_kmh) * 60)


def generate_request_id() -> str:
    return str(uuid.uuid4())


def round_coords(lat: float, lng: float, precision: int = 3) -> tuple[str, str]:
    """Round coordinates for cache key generation."""
    return str(round(lat, precision)), str(round(lng, precision))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_success_response(data: dict, **meta_extra) -> dict:
    meta = {"timestamp": now_iso(), "request_id": generate_request_id()}
    meta.update(meta_extra)
    return {"success": True, "data": data, "meta": meta}


def build_error_response(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}
