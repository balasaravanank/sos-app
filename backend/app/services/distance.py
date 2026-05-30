import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
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
    """Estimate arrival time. Default 40 km/h for urban emergency vehicles."""
    if speed_kmh <= 0:
        return 0
    return round((distance_km / speed_kmh) * 60)


def sort_by_distance(
    services: list[dict], lat: float, lng: float
) -> list[dict]:
    """Add distance_km to each service and sort ascending."""
    for svc in services:
        svc["distance_km"] = round(
            haversine_km(lat, lng, svc["lat"], svc["lng"]), 2
        )
    return sorted(services, key=lambda s: s["distance_km"])
