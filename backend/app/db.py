import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

_engine = None
_SessionLocal = None
_db_available = False

Base = declarative_base()


def _try_create_engine():
    """Attempt to create DB engine. Skip silently if URL is placeholder."""
    global _engine, _SessionLocal
    if not DATABASE_URL or DATABASE_URL == "mock" or "user:pass@" in DATABASE_URL:
        logger.info("DATABASE_URL not configured — running without database")
        return

    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# Try on module load
_try_create_engine()


def get_db():
    """FastAPI dependency — yields a DB session. Returns None if DB not configured."""
    if _SessionLocal is None:
        yield None
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if engine is available. Handles connection errors gracefully."""
    global _db_available
    if _engine is None:
        logger.info("No DB engine — skipping table creation")
        return

    try:
        Base.metadata.create_all(bind=_engine)
        _db_available = True
        logger.info("Database tables verified")
    except Exception as e:
        logger.warning(f"Database connection failed: {e} — running without database")
        _db_available = False
