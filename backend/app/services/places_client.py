import os
import logging
import httpx
from app.schemas.services import ServiceItem

logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Google Places type mapping
TYPE_MAP = {
    "hospital": "hospital",
    "police": "police",
    "ambulance": "hospital",  # No direct type — use keyword search
    "towing": "car_repair",
    "puncture": "car_repair",
}

KEYWORD_MAP = {
    "ambulance": "ambulance service",
    "towing": "towing vehicle recovery",
    "puncture": "tyre puncture repair",
}


class PlacesUnavailableError(Exception):
    """Raised when Google Places API cannot be reached or has no key."""
    pass


async def search_nearby(
    lat: float, lng: float, service_type: str, radius: int = 5000
) -> list[dict]:
    """
    Query Google Places Nearby Search API.
    Returns normalized list of service dicts.
    Raises PlacesUnavailableError on any failure.
    """
    if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "mock":
        raise PlacesUnavailableError("No Google Places API key configured")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": TYPE_MAP.get(service_type, service_type),
        "key": GOOGLE_PLACES_API_KEY,
    }

    # Add keyword for types that need more specific results
    keyword = KEYWORD_MAP.get(service_type)
    if keyword:
        params["keyword"] = keyword

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            error_msg = data.get("error_message", data.get("status", "Unknown error"))
            raise PlacesUnavailableError(f"Places API error: {error_msg}")

        results = data.get("results", [])
        return [_normalize_place(place, service_type) for place in results[:20]]

    except httpx.HTTPError as e:
        raise PlacesUnavailableError(f"Places API request failed: {e}")


def _normalize_place(place: dict, service_type: str) -> dict:
    """Convert Google Places result to our standard shape."""
    location = place.get("geometry", {}).get("location", {})

    # Try to extract phone from details (not always in nearby search)
    phone = place.get("formatted_phone_number")

    return {
        "name": place.get("name", "Unknown"),
        "address": place.get("vicinity", ""),
        "phone": phone or "",
        "lat": location.get("lat", 0),
        "lng": location.get("lng", 0),
        "type": service_type,
        "rating": place.get("rating"),
        "place_id": place.get("place_id"),
        "distance_km": None,  # Calculated later by distance.sort_by_distance
    }
