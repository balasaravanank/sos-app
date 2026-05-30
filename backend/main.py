import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load the shared .env file from the project root
load_dotenv(dotenv_path="../.env")

from app.routes import sos, location, dispatch, services
from app.db import init_db
from app.utils import build_error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Emergency SOS & ROADSoS API",
    version="1.0.0",
    description="Backend API for Emergency SOS triggers, dispatch coordination, and ROADSoS services lookup.",
)

# CORS — allow frontend origin
cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sos.router, prefix="/api/sos", tags=["SOS"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(dispatch.router, prefix="/api/dispatch", tags=["Dispatch"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])


@app.on_event("startup")
def on_startup():
    init_db()
    logging.getLogger(__name__).info("Database initialized")


@app.get("/ping")
def ping():
    return {"success": True, "message": "server alive"}


@app.get("/")
def read_root():
    return {"message": "Welcome to SOS App API"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=build_error_response("INTERNAL_ERROR", "An unexpected error occurred"),
    )
