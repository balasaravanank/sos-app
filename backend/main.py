from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from app.request_id_middleware import RequestIdMiddleware
from app.routes import sos, location, dispatch, services, cache
from app.init_db import init_db

app = FastAPI(title="Emergency SOS & ROADSoS API", version="1.0.0")

# Middlewares
app.add_middleware(RequestIdMiddleware)

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN] if CORS_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(sos.router, prefix="/api/sos", tags=["SOS"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(dispatch.router, prefix="/api/dispatch", tags=["Dispatch"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache"])

@app.on_event("startup")
async def startup_event():
    # Initialize DB tables
    try:
        await init_db()
        print("Database tables initialized")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

@app.get("/ping", tags=["Health"])
async def ping(request: Request):
    from app.routes.location import wrap_response
    return wrap_response(request, data={"success": True})
