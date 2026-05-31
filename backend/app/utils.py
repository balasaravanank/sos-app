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


def sort_by_distance(services: list[dict], lat: float, lng: float) -> list[dict]:
    """Add distance_km to each service and sort ascending."""
    for svc in services:
        svc["distance_km"] = round(
            haversine_km(lat, lng, svc["lat"], svc["lng"]), 2
        )
    return sorted(services, key=lambda s: s["distance_km"])


def round_coords(lat: float, lng: float, precision: int = 3) -> tuple[str, str]:
    """Round coordinates for cache key generation."""
    return str(round(lat, precision)), str(round(lng, precision))


# ---------------------------------------------------------------------------
# Standard API Response Envelope
# ---------------------------------------------------------------------------

def generate_request_id() -> str:
    """Generate a short unique request ID for tracing."""
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def success_response(data: Any, request_id: str | None = None) -> dict:
    """Wrap data in the standard success envelope."""
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": now_iso(),
            "request_id": request_id or generate_request_id(),
        },
    }


def build_success_response(data: dict, **meta_extra) -> dict:
    """Wrap data in the standard success envelope with extra meta fields."""
    meta = {"timestamp": now_iso(), "request_id": generate_request_id()}
    meta.update(meta_extra)
    return {"success": True, "data": data, "meta": meta}


def error_response(code: str, message: str) -> dict:
    """Wrap error info in the standard error envelope."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


# Alias for compatibility with roadsos-services
build_error_response = error_response
