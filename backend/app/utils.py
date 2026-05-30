"""Shared utilities — distance calculation, ETA, and standard API response helpers."""

import math
import uuid
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Distance & ETA
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two GPS coordinates using Haversine formula."""
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


def eta_minutes(distance_km: float, speed_kmh: float = 40.0) -> int:
    """Estimate arrival time in minutes. Default 40 km/h for urban ambulance."""
    if speed_kmh <= 0:
        return 0
    return max(1, round((distance_km / speed_kmh) * 60))


# ---------------------------------------------------------------------------
# Standard API Response Envelope
# ---------------------------------------------------------------------------

def generate_request_id() -> str:
    """Generate a short unique request ID for tracing."""
    return uuid.uuid4().hex[:12]


def success_response(data: Any, request_id: str | None = None) -> dict:
    """Wrap data in the standard success envelope."""
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id or generate_request_id(),
        },
    }


def error_response(code: str, message: str) -> dict:
    """Wrap error info in the standard error envelope."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
