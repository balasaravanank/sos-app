"""SQLAlchemy model for the services_cache table.

Used as fallback when Google Places API is unavailable.
Stores nearby hospitals, trauma centers, etc. for offline/fallback queries.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class ServiceCache(Base):
    __tablename__ = "services_cache"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # hospital | police | ambulance | towing
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    distance: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
