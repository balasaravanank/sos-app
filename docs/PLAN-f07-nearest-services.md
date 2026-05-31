# F-07: Nearest Services (ROADSoS) — Dev-4 Backend Implementation

> **Feature:** F-07 — Nearest Services (ROADSoS Location Tool)
> **Priority:** P0 — Must Have
> **Branch:** `dev4/roadsos-services`
> **Owner:** Dev-4
> **Stack:** FastAPI (Python) · Supabase PostgreSQL · Upstash Redis · Google Places API

---

## Context

The Emergency SOS & ROADSoS platform needs a location-based service lookup engine — the **ROADSoS module**. When an accident, injury, or safety incident occurs, users need to instantly find the nearest trauma centers, hospitals, police stations, ambulance services, and towing providers.

**F-07 is the backend brain of the ROADSoS tool.** It receives coordinates and returns a normalized list of nearby emergency services, powered by Google Places API with a local database fallback for resilience.

### Current State

| File | Status |
|------|--------|
| [services.py](file:///c:/Users/admin/sos-app/backend/app/routes/services.py) | Empty — router stub only |
| [db.py](file:///c:/Users/admin/sos-app/backend/app/db.py) | Empty — placeholder comment |
| [redis.py](file:///c:/Users/admin/sos-app/backend/app/redis.py) | Empty — placeholder comment |
| [main.py](file:///c:/Users/admin/sos-app/backend/main.py) | Basic FastAPI app — no CORS, no route imports |
| `backend/app/models/` | Does not exist |
| `backend/app/schemas/` | Does not exist |
| `backend/app/services/` | Does not exist |

---

## User Review Required

> [!IMPORTANT]
> **Google Places API Key** — The Google Places API (New) requires a valid API key with Places API enabled in Google Cloud Console. Do you already have one, or should the implementation default to **DB-fallback-only mode** with seeded data for now?

> [!IMPORTANT]
> **Supabase vs Local PostgreSQL** — The MVP doc specifies Supabase (managed PostgreSQL). Do you have a Supabase project set up, or should we target local PostgreSQL via Docker? This affects the `DATABASE_URL` format and connection pooling.

> [!IMPORTANT]
> **Upstash Redis vs Local Redis** — The docs specify Upstash (HTTP-based managed Redis). Do you have Upstash credentials, or should we use local Redis / in-memory fallback for caching?

---

## Open Questions

> [!WARNING]
> **Scope boundary** — The PRD lists `RS-05 Vehicle Rescue` (P1) and `RS-06 Puncture Shops` (P2) as additional service types. Should F-07 include these in the `types` endpoint and schema, or strictly limit to P0 types only (`hospital`, `police`, `ambulance`)?

> [!NOTE]
> **Rate limiting** — The PRD mentions rate limiting for SOS endpoints, but not explicitly for services lookup. Should we add rate limiting to `GET /api/services/nearby` to prevent Google Places API abuse? (I recommend yes — 60 requests/min/user.)

---

## Proposed Changes

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                   API Layer (Router)                   │
│   GET /nearby  ·  GET /types  ·  GET /:id  ·  GET /offline-pack  │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│               Service Layer (Business Logic)           │
│   NearbyServiceLookup  ·  Cache Strategy  ·  Fallback │
└───────┬────────────────────────────┬─────────────────┘
        │                            │
┌───────▼──────┐            ┌────────▼────────┐
│ Google Places │            │  PostgreSQL DB   │
│   API Client  │            │ (services_cache) │
└───────┬──────┘            └────────┬────────┘
        │                            │
        └──────────┬─────────────────┘
                   │
            ┌──────▼──────┐
            │ Upstash Redis │
            │  (TTL Cache)  │
            └─────────────┘
```

**Data flow:**
1. Request arrives → Check Redis cache (key: `nearby:{lat_rounded}:{lng_rounded}:{type}`)
2. Cache **hit** → Return cached data immediately
3. Cache **miss** → Call Google Places API
4. Places API **success** → Normalize response, save to Redis (6h TTL) + save to `services_cache` DB table, return
5. Places API **failure** (no key, quota exceeded, network error) → Query `services_cache` DB table by haversine distance, return

---

### Infrastructure Layer

#### [NEW] [db.py](file:///c:/Users/admin/sos-app/backend/app/db.py)
- Supabase/PostgreSQL async connection using `sqlalchemy.ext.asyncio`
- Connection pool with `asyncpg` driver
- `get_db()` dependency for FastAPI route injection
- Read `DATABASE_URL` from environment

#### [NEW] [redis.py](file:///c:/Users/admin/sos-app/backend/app/redis.py)
- Upstash Redis HTTP client using `httpx` (or `redis` library for local)
- `get_redis()` helper with graceful fallback to in-memory `dict` if Redis unavailable
- Helper methods: `cache_get(key)`, `cache_set(key, value, ttl_seconds)`

#### [MODIFY] [main.py](file:///c:/Users/admin/sos-app/backend/main.py)
- Add CORS middleware with `CORS_ORIGIN` from `.env`
- Import and register all 4 routers with proper prefixes
- Add `/ping` health check endpoint
- Add global exception handler for standard error envelope
- Add startup/shutdown events for DB pool and Redis connection

---

### Models Layer

#### [NEW] `backend/app/models/__init__.py`
- Empty init for package

#### [NEW] `backend/app/models/services.py`
- SQLAlchemy model: `ServiceCache`
  - `id` (UUID, PK)
  - `lat` (Numeric 10,7)
  - `lng` (Numeric 10,7)
  - `type` (String — `hospital` | `police` | `ambulance` | `towing` | `puncture`)
  - `name` (String)
  - `phone` (String, nullable)
  - `address` (String)
  - `rating` (Float, nullable)
  - `place_id` (String, nullable — Google Places ID for dedup)
  - `distance` (Numeric 10,2, nullable — computed at query time)
  - `cached_at` (DateTime, default `now()`)

---

### Schemas Layer

#### [NEW] `backend/app/schemas/__init__.py`
- Empty init for package

#### [NEW] `backend/app/schemas/services.py`
- Pydantic models:

```python
class ServiceItem(BaseModel):
    name: str
    address: str
    phone: str | None
    distance_km: float
    lat: float
    lng: float
    type: str
    rating: float | None = None
    place_id: str | None = None

class NearbyParams(BaseModel):
    lat: float = Query(..., ge=-90, le=90)
    lng: float = Query(..., ge=-180, le=180)
    type: str = Query("hospital", regex="^(hospital|police|ambulance|towing|puncture)$")
    radius: int = Query(5000, ge=500, le=50000)

class NearbyResponse(BaseModel):
    success: bool = True
    data: dict  # { services: list[ServiceItem] }
    meta: dict  # { timestamp, request_id, source, count }

class ServiceDetailResponse(BaseModel):
    success: bool = True
    data: ServiceItem
    meta: dict

class TypesResponse(BaseModel):
    success: bool = True
    data: dict  # { types: list[str] }

class OfflinePackResponse(BaseModel):
    success: bool = True
    data: dict  # { services: list[ServiceItem], cached_at: str }
    meta: dict
```

---

### Service Layer

#### [NEW] `backend/app/services/__init__.py`
- Empty init for package

#### [NEW] `backend/app/services/places_client.py`
- Google Places Nearby Search integration
- `search_nearby(lat, lng, type, radius) -> list[ServiceItem]`
- Maps Google Places types:
  - `hospital` → `"hospital"`
  - `police` → `"police"`
  - `ambulance` → `"ambulance_service"` (custom keyword search)
  - `towing` → `"car_repair"` (keyword: "towing")
- Normalizes Google response → `ServiceItem` shape
- Handles: no API key, quota exceeded, network errors → raises `PlacesUnavailableError`

#### [NEW] `backend/app/services/nearby_lookup.py`
- Core business logic orchestrator
- `find_nearby(lat, lng, type, radius, db, redis) -> list[ServiceItem]`
- Flow:
  1. Round coords to 3 decimal places for cache key
  2. Check Redis → return if hit
  3. Try Google Places → normalize → cache in Redis (TTL 6h) + upsert to DB
  4. On Places failure → query `services_cache` table using haversine
  5. Sort by distance ascending
  6. Return normalized list

#### [NEW] `backend/app/services/distance.py`
- `haversine_km(lat1, lng1, lat2, lng2) -> float`
- `eta_minutes(distance_km, speed_kmh=40) -> int`
- Shared utility — also used by Dev-3 (dispatch)

---

### Route Layer (The Main Feature)

#### [MODIFY] [services.py](file:///c:/Users/admin/sos-app/backend/app/routes/services.py)

**4 endpoints:**

##### `GET /api/services/nearby`
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `lat` | float | ✅ | — | Latitude (-90 to 90) |
| `lng` | float | ✅ | — | Longitude (-180 to 180) |
| `type` | string | ❌ | `hospital` | Service type filter |
| `radius` | int | ❌ | `5000` | Search radius in meters (500–50000) |

**Response:**
```json
{
  "success": true,
  "data": {
    "services": [
      {
        "name": "Apollo Hospitals",
        "address": "Greams Rd, Chennai",
        "phone": "+91-44-28290200",
        "distance_km": 1.2,
        "lat": 13.0615,
        "lng": 80.2519,
        "type": "hospital",
        "rating": 4.3,
        "place_id": "ChIJ..."
      }
    ]
  },
  "meta": {
    "timestamp": "2026-05-30T08:00:00Z",
    "request_id": "uuid",
    "source": "google_places",
    "count": 5
  }
}
```

**Error cases:**
- Missing `lat`/`lng` → `400` + `LOCATION_MISSING`
- Invalid `type` → `400` + `INVALID_SERVICE_TYPE`
- No results found → `200` + empty `services` array (not 404)

---

##### `GET /api/services/types`
No params. Returns available service type filters.

```json
{
  "success": true,
  "data": {
    "types": ["hospital", "police", "ambulance", "towing", "puncture"]
  },
  "meta": { "timestamp": "..." }
}
```

---

##### `GET /api/services/{service_id}`
Returns detail for a single cached service by UUID.

```json
{
  "success": true,
  "data": {
    "name": "Apollo Hospitals",
    "address": "Greams Rd, Chennai",
    "phone": "+91-44-28290200",
    "distance_km": null,
    "lat": 13.0615,
    "lng": 80.2519,
    "type": "hospital",
    "rating": 4.3
  },
  "meta": { "timestamp": "..." }
}
```

**Error:** Invalid/missing ID → `404` + `SERVICE_NOT_FOUND`

---

##### `GET /api/services/offline-pack`
Pre-packages all service types for the user's current location. Frontend stores this in `localStorage` on app load.

| Param | Type | Required | Default |
|-------|------|----------|---------|
| `lat` | float | ✅ | — |
| `lng` | float | ✅ | — |

```json
{
  "success": true,
  "data": {
    "services": [ /* all types combined */ ],
    "cached_at": "2026-05-30T08:00:00Z"
  },
  "meta": {
    "timestamp": "...",
    "request_id": "...",
    "types_included": ["hospital", "police", "ambulance"],
    "total_count": 15
  }
}
```

---

### Utility Layer

#### [NEW] `backend/app/utils.py`
- `haversine_km()` — shared distance calculator
- `eta_minutes()` — ETA estimation
- `generate_request_id()` — UUID4 for response meta
- `round_coords(lat, lng, precision=3)` — for cache key generation
- `build_success_response(data, **meta)` — standard envelope builder
- `build_error_response(code, message, status)` — standard error builder

---

### Seed Data

#### [NEW] `backend/seed_services.sql`
Static service data for Chennai (fallback when Google Places unavailable):

- 5 hospitals (Apollo, MIOT, Fortis, Government General, Sri Ramachandra)
- 5 police stations (one per zone: central, south, north, west, east)
- 5 ambulance services
- 3 towing services
- 2 puncture shops

All with real-ish Chennai coordinates, phone numbers, and addresses.

---

### Environment Configuration

#### [MODIFY] [.env](file:///c:/Users/admin/sos-app/.env)
Add required variables:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres
REDIS_URL=https://your-redis.upstash.io
REDIS_TOKEN=your_upstash_token
GOOGLE_PLACES_API_KEY=your_key_here
PORT=8000
CORS_ORIGIN=http://localhost:5173
```

---

### Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/admin/sos-app/backend/requirements.txt)
Add missing packages:

```diff
 fastapi
 uvicorn
 python-dotenv
 sqlalchemy
 pydantic
 redis
+asyncpg
+httpx
+uuid6
```

---

## File Creation Summary

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `backend/app/utils.py` | NEW | Haversine, response builders, helpers |
| 2 | `backend/app/models/__init__.py` | NEW | Package init |
| 3 | `backend/app/models/services.py` | NEW | SQLAlchemy `ServiceCache` model |
| 4 | `backend/app/schemas/__init__.py` | NEW | Package init |
| 5 | `backend/app/schemas/services.py` | NEW | Pydantic request/response schemas |
| 6 | `backend/app/services/__init__.py` | NEW | Package init |
| 7 | `backend/app/services/places_client.py` | NEW | Google Places API client |
| 8 | `backend/app/services/nearby_lookup.py` | NEW | Core lookup orchestrator |
| 9 | `backend/app/services/distance.py` | NEW | Distance calculation utility |
| 10 | `backend/app/db.py` | MODIFY | Async DB connection + pool |
| 11 | `backend/app/redis.py` | MODIFY | Redis client with fallback |
| 12 | `backend/app/routes/services.py` | MODIFY | 4 API endpoints |
| 13 | `backend/main.py` | MODIFY | CORS, routers, error handler |
| 14 | `backend/requirements.txt` | MODIFY | Add asyncpg, httpx |
| 15 | `backend/seed_services.sql` | NEW | Fallback seed data |
| 16 | `.env` | MODIFY | Add env variables |

---

## Verification Plan

### Automated Tests (FastAPI /docs)

| # | Endpoint | Test Scenario | Expected Result |
|---|----------|---------------|-----------------|
| 1 | `GET /api/services/nearby?lat=13.08&lng=80.27&type=hospital` | Valid request with all params | `200` — array of hospitals sorted by distance |
| 2 | `GET /api/services/nearby?type=hospital` | Missing `lat`/`lng` | `400` + `LOCATION_MISSING` |
| 3 | `GET /api/services/nearby?lat=13.08&lng=80.27&type=invalid` | Invalid type value | `400` + `INVALID_SERVICE_TYPE` |
| 4 | `GET /api/services/nearby?lat=13.08&lng=80.27&type=hospital` | No Google API key — DB fallback | `200` — returns seeded data, `meta.source = "database"` |
| 5 | `GET /api/services/types` | No params | `200` — returns types array |
| 6 | `GET /api/services/{valid_uuid}` | Existing service ID | `200` — full service detail |
| 7 | `GET /api/services/{invalid_uuid}` | Non-existent ID | `404` + `SERVICE_NOT_FOUND` |
| 8 | `GET /api/services/offline-pack?lat=13.08&lng=80.27` | Valid request | `200` — combined services from all types |

### Manual Verification

- Start server with `uvicorn main:app --reload --port 8000`
- Open `http://localhost:8000/docs` — confirm all 4 endpoints render in Swagger UI
- Test each endpoint via Swagger interactive UI
- Remove `GOOGLE_PLACES_API_KEY` from `.env` → restart → confirm DB fallback works seamlessly
- Check Redis caching: call same endpoint twice → second call should be faster and `meta.source = "cache"`
