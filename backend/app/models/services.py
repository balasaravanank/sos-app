import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Float, DateTime
from app.db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class ServiceCache(Base):
    __tablename__ = "services_cache"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lat = Column(Numeric(10, 7), nullable=False)
    lng = Column(Numeric(10, 7), nullable=False)
    type = Column(String, nullable=False)  # hospital | police | ambulance | towing | puncture
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    place_id = Column(String, nullable=True)  # Google Places ID for dedup
    distance = Column(Numeric(10, 2), nullable=True)
    cached_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address or "",
            "phone": self.phone or "",
            "lat": float(self.lat),
            "lng": float(self.lng),
            "type": self.type,
            "rating": self.rating,
            "place_id": self.place_id,
            "distance_km": float(self.distance) if self.distance else None,
        }
