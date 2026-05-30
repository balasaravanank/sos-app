"""SQLAlchemy model for the dispatch_units table.

Read-only for Dev-1 — used to find nearest police/ambulance units.
Seeded in Supabase with mock data (10 units across Chennai zones).
"""

import uuid
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class DispatchUnit(Base):
    __tablename__ = "dispatch_units"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    type: Mapped[str] = mapped_column(String, nullable=False)  # ambulance | police
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    status: Mapped[str] = mapped_column(String, default="available")
    zone: Mapped[str | None] = mapped_column(String, nullable=True)
    contact: Mapped[str | None] = mapped_column(String, nullable=True)
