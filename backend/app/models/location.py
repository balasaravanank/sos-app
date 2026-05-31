import uuid
from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from app.db import Base
from datetime import datetime, timezone

class LocationHistory(Base):
    __tablename__ = "location_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    sos_id = Column(UUID(as_uuid=True), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    source = Column(String(20), default="gps")
    geom = Column(Geography(geometry_type='POINT', srid=4326))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
