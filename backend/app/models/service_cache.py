"""SQLAlchemy model for the services_cache table.

Used as fallback when Google Places API is unavailable.
Stores nearby hospitals, trauma centers, etc. for offline/fallback queries.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class ServiceCache(Base):
    __tablename__ = "services_cache"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # hospital | police | ambulance | towing | puncture
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    place_id: Mapped[str | None] = mapped_column(String, nullable=True)  # Google Places ID for dedup
    distance: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        """Convert to standard service dict for API responses."""
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
