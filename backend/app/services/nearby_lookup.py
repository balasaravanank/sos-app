import logging
from sqlalchemy.orm import Session

from app.services.places_client import search_nearby, PlacesUnavailableError
from app.services.distance import sort_by_distance
from app.models.services import ServiceCache
from app.redis import cache_get, cache_set
from app.utils import round_coords

logger = logging.getLogger(__name__)

CACHE_TTL = 21600  # 6 hours


def _cache_key(lat: float, lng: float, service_type: str) -> str:
    lat_r, lng_r = round_coords(lat, lng, precision=3)
    return f"nearby:{lat_r}:{lng_r}:{service_type}"


async def find_nearby(
    lat: float,
    lng: float,
    service_type: str,
    radius: int,
    db: Session | None,
) -> tuple[list[dict], str]:
    """
    Find nearby services. Returns (services_list, source_label).

    Flow:
    1. Check Redis cache
    2. Try Google Places API
    3. Fall back to DB (services_cache table)
    """
    key = _cache_key(lat, lng, service_type)

    # Step 1: Redis cache check
    cached = cache_get(key)
    if cached:
        logger.info(f"Cache HIT for {key}")
        return cached, "cache"

    # Step 2: Try Google Places
    try:
        services = await search_nearby(lat, lng, service_type, radius)
        services = sort_by_distance(services, lat, lng)

        # Cache the result
        cache_set(key, services, CACHE_TTL)

        # Persist to DB for future fallback
        if db and services:
            _upsert_to_db(db, services)

        logger.info(f"Google Places returned {len(services)} results for {service_type}")
        return services, "google_places"

    except PlacesUnavailableError as e:
        logger.warning(f"Places unavailable: {e} — falling back to DB")

    # Step 3: DB fallback
    services = _query_db(db, lat, lng, service_type, radius)
    services = sort_by_distance(services, lat, lng)

    # Cache DB results too (shorter TTL)
    if services:
        cache_set(key, services, CACHE_TTL // 2)

    logger.info(f"DB fallback returned {len(services)} results for {service_type}")
    return services, "database"


def _query_db(
    db: Session | None,
    lat: float,
    lng: float,
    service_type: str,
    radius: int,
) -> list[dict]:
    """Query services_cache table filtered by type. Distance filtered in Python."""
    if db is None:
        return _get_hardcoded_fallback(service_type)

    try:
        rows = (
            db.query(ServiceCache)
            .filter(ServiceCache.type == service_type)
            .all()
        )

        radius_km = radius / 1000
        results = []
        for row in rows:
            d = row.to_dict()
            from app.services.distance import haversine_km
            dist = haversine_km(lat, lng, d["lat"], d["lng"])
            if dist <= radius_km:
                d["distance_km"] = round(dist, 2)
                results.append(d)

        return results

    except Exception as e:
        logger.error(f"DB query failed: {e}")
        return _get_hardcoded_fallback(service_type)


def _upsert_to_db(db: Session, services: list[dict]) -> None:
    """Persist Google Places results to services_cache for future fallback."""
    try:
        for svc in services:
            place_id = svc.get("place_id")
            if place_id:
                existing = (
                    db.query(ServiceCache)
                    .filter(ServiceCache.place_id == place_id)
                    .first()
                )
                if existing:
                    existing.name = svc["name"]
                    existing.address = svc.get("address", "")
                    existing.phone = svc.get("phone", "")
                    existing.rating = svc.get("rating")
                    continue

            entry = ServiceCache(
                lat=svc["lat"],
                lng=svc["lng"],
                type=svc["type"],
                name=svc["name"],
                phone=svc.get("phone", ""),
                address=svc.get("address", ""),
                rating=svc.get("rating"),
                place_id=place_id,
            )
            db.add(entry)

        db.commit()
    except Exception as e:
        logger.error(f"DB upsert failed: {e}")
        db.rollback()


def get_service_by_id(db: Session | None, service_id: str) -> dict | None:
    """Look up a single service by its UUID."""
    if db is None:
        return None
    try:
        row = db.query(ServiceCache).filter(ServiceCache.id == service_id).first()
        return row.to_dict() if row else None
    except Exception as e:
        logger.error(f"Service lookup failed: {e}")
        return None


async def get_offline_pack(
    lat: float, lng: float, db: Session | None
) -> tuple[list[dict], list[str]]:
    """Fetch all service types for offline caching."""
    from app.schemas.services import VALID_SERVICE_TYPES

    all_services = []
    types_found = []

    for svc_type in ["hospital", "police", "ambulance"]:  # P0 types only
        services, _ = await find_nearby(lat, lng, svc_type, 10000, db)
        if services:
            all_services.extend(services)
            types_found.append(svc_type)

    return all_services, types_found


def _get_hardcoded_fallback(service_type: str) -> list[dict]:
    """Last-resort hardcoded data when both Places and DB are unavailable."""
    fallback = {
        "hospital": [
            {"name": "Apollo Hospitals Greams Road", "address": "21 Greams Ln, Chennai 600006", "phone": "+91-44-28290200", "lat": 13.0615, "lng": 80.2519, "type": "hospital", "rating": 4.3, "distance_km": None, "place_id": None},
            {"name": "Government General Hospital", "address": "Park Town, Chennai 600003", "phone": "+91-44-25305000", "lat": 13.0878, "lng": 80.2785, "type": "hospital", "rating": 3.5, "distance_km": None, "place_id": None},
        ],
        "police": [
            {"name": "Central Police Station", "address": "Egmore, Chennai 600008", "phone": "100", "lat": 13.0827, "lng": 80.2707, "type": "police", "rating": None, "distance_km": None, "place_id": None},
        ],
        "ambulance": [
            {"name": "GVK EMRI 108 Ambulance", "address": "Central Chennai", "phone": "108", "lat": 13.0827, "lng": 80.2707, "type": "ambulance", "rating": None, "distance_km": None, "place_id": None},
        ],
        "towing": [
            {"name": "AAA Towing Services", "address": "Kodambakkam, Chennai 600024", "phone": "+91-98400-12345", "lat": 13.0700, "lng": 80.2400, "type": "towing", "rating": 3.8, "distance_km": None, "place_id": None},
        ],
        "puncture": [
            {"name": "Sri Ganesh Tyre Works", "address": "Egmore, Chennai 600008", "phone": "+91-98765-43210", "lat": 13.0800, "lng": 80.2650, "type": "puncture", "rating": 4.0, "distance_km": None, "place_id": None},
        ],
    }
    return fallback.get(service_type, [])
