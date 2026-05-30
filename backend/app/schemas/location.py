from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class LocationUpdateRequest(BaseModel):
    user_id: UUID
    sos_id: Optional[UUID] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy: float = Field(..., gt=0, le=500)

class LocationStopRequest(BaseModel):
    user_id: UUID
    sos_id: UUID

class LocationResponse(BaseModel):
    lat: float
    lng: float
    accuracy: float
    timestamp: str

class CachedLocationResponse(BaseModel):
    lat: float
    lng: float
    cached_at: str

class EmergencyContact(BaseModel):
    name: str
    phone: str
