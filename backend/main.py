"""Emergency SOS & ROADSoS — FastAPI Entry Point.

Registers all route modules. Creates tables + seeds mock data on startup.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path="../.env")

from app.db import init_db, AsyncSessionLocal
from app.models import SOSEvent, DispatchUnit, ServiceCache  # noqa: F401 — registers models
from app.routes import sos, location, dispatch, services, cache
from app.request_id_middleware import RequestIdMiddleware

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("sos-api")


# ---------------------------------------------------------------------------
# Seed mock data (runs once if tables are empty)
# ---------------------------------------------------------------------------

async def seed_mock_data():
    """Insert mock dispatch units + services if tables are empty."""
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        # Check if dispatch_units already has data
        result = await db.execute(select(func.count()).select_from(DispatchUnit))
        count = result.scalar()
        if count and count > 0:
            logger.info("Seed: dispatch_units already has %d rows — skipping", count)
            return

        logger.info("Seed: inserting mock dispatch units + services...")

        # 5 ambulances + 5 police stations across Chennai zones
        units = [
            DispatchUnit(type="ambulance", lat=13.0827, lng=80.2707, zone="central", contact="108", status="available"),
            DispatchUnit(type="ambulance", lat=13.0500, lng=80.2100, zone="south", contact="108", status="available"),
            DispatchUnit(type="ambulance", lat=13.1200, lng=80.2800, zone="north", contact="108", status="available"),
            DispatchUnit(type="ambulance", lat=13.0900, lng=80.2400, zone="west", contact="108", status="available"),
            DispatchUnit(type="ambulance", lat=13.0600, lng=80.2600, zone="east", contact="108", status="available"),
            DispatchUnit(type="police", lat=13.0827, lng=80.2707, zone="central", contact="100", status="available"),
            DispatchUnit(type="police", lat=13.0500, lng=80.2100, zone="south", contact="100", status="available"),
            DispatchUnit(type="police", lat=13.1200, lng=80.2800, zone="north", contact="100", status="available"),
            DispatchUnit(type="police", lat=13.0900, lng=80.2400, zone="west", contact="100", status="available"),
            DispatchUnit(type="police", lat=13.0600, lng=80.2600, zone="east", contact="100", status="available"),
        ]

        # Mock hospitals/trauma centers for F-02 (Injury SOS) fallback
        services_data = [
            ServiceCache(type="hospital", lat=13.0860, lng=80.2750, name="Apollo Hospital - Greams Road", phone="+914428293333", address="21 Greams Lane, Chennai"),
            ServiceCache(type="hospital", lat=13.0670, lng=80.2580, name="MIOT International", phone="+914442002288", address="4/112 Mount Poonamallee Rd, Chennai"),
            ServiceCache(type="hospital", lat=13.0480, lng=80.2170, name="Fortis Malar Hospital", phone="+914442891010", address="52 1st Main Rd, Adyar, Chennai"),
            ServiceCache(type="hospital", lat=13.0780, lng=80.2820, name="Rajiv Gandhi Govt Hospital", phone="+914425305000", address="EVR Periyar Salai, Chennai"),
            ServiceCache(type="hospital", lat=13.1050, lng=80.2920, name="Stanley Medical College Hospital", phone="+914425281343", address="Old Jail Rd, Royapuram, Chennai"),
        ]

        db.add_all(units + services_data)
        await db.commit()
        logger.info("Seed: inserted %d dispatch units + %d services", len(units), len(services_data))


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SOS API starting — port %s", os.getenv("PORT", "8000"))
    await init_db()
    await seed_mock_data()
    yield
    logger.info("SOS API shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Emergency SOS & ROADSoS API",
    description="Backend for the Emergency SOS platform — F-01 to F-08",
    version="1.0.0",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(RequestIdMiddleware)

cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

app.include_router(sos.router, prefix="/api/sos", tags=["SOS"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(dispatch.router, prefix="/api/dispatch", tags=["Dispatch"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/ping")
async def ping():
    return {"success": True, "message": "server alive"}


@app.get("/")
async def root():
    return {"success": True, "message": "Emergency SOS & ROADSoS API v1.0"}


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
        },
    )
