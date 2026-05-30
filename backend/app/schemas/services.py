from pydantic import BaseModel, Field
from typing import Optional


class ServiceItem(BaseModel):
    name: str
    address: str = ""
    phone: Optional[str] = None
    distance_km: Optional[float] = None
    lat: float
    lng: float
    type: str
    rating: Optional[float] = None
    place_id: Optional[str] = None
    id: Optional[str] = None


class NearbyServicesData(BaseModel):
    services: list[ServiceItem] = []


class ServiceTypesData(BaseModel):
    types: list[str] = []


class OfflinePackData(BaseModel):
    services: list[ServiceItem] = []
    cached_at: str = ""


class MetaInfo(BaseModel):
    timestamp: str
    request_id: str
    source: Optional[str] = None
    count: Optional[int] = None
    types_included: Optional[list[str]] = None
    total_count: Optional[int] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict
    meta: dict


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


VALID_SERVICE_TYPES = ["hospital", "police", "ambulance", "towing", "puncture"]
