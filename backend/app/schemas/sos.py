"""Pydantic schemas for SOS endpoints — request validation and response contracts."""

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class SOSTriggerRequest(BaseModel):
    """Unified request body for POST /api/sos/trigger."""
    type: Literal["emergency", "injury", "safety"] = Field(
        ..., description="SOS type: emergency (red), injury (yellow), safety (green)"
    )
    lat: float = Field(..., ge=-90, le=90, description="Latitude — required")
    lng: float = Field(..., ge=-180, le=180, description="Longitude — required")
    user_id: str | None = Field(None, description="User identifier (optional on Day 1)")
    timestamp: str | None = Field(None, description="ISO 8601 timestamp from client")


class SOSConfirmRequest(BaseModel):
    """Request body for POST /api/sos/{sos_id}/confirm — crowd confirmation."""
    user_id: str = Field(..., description="Confirming user's ID")
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


# ---------------------------------------------------------------------------
# Response Data Schemas (nested inside the standard envelope)
# ---------------------------------------------------------------------------

class EmergencySOSData(BaseModel):
    """Response data for type='emergency' (F-01)."""
    sos_id: str
    status: str = "active"
    eta_message: str = "Help is on the way"
    nearest_ambulance: dict | None = None  # { unit_id, eta_mins, contact }


class InjurySOSData(BaseModel):
    """Response data for type='injury' (F-02)."""
    sos_id: str
    nearest_trauma_center: dict | None = None  # { name, address, phone, distance }
    directions_url: str | None = None


class SafetySOSData(BaseModel):
    """Response data for type='safety' (F-03)."""
    sos_id: str
    police_notified: bool = True
    nearest_station: dict | None = None  # { station_id, name, contact, eta_mins }


class SOSConfirmData(BaseModel):
    """Response data for crowd confirmation."""
    confirmed_by: int
    verified: bool  # True if confirmed_by >= 2


class SOSStatusData(BaseModel):
    """Response data for GET /api/sos/{sos_id}/status."""
    sos_id: str
    type: str
    status: str
    confirmed_by: int
    created_at: str
