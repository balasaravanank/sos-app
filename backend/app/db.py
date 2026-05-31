"""Database connection — async SQLAlchemy engine.

Priority: Supabase PostgreSQL if DATABASE_URL is valid.
Fallback: Local SQLite (aiosqlite) for offline development.
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Determine connection string — handle all common URL prefixes
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    _url = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    logger.info("Database: Supabase PostgreSQL")
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    _url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    logger.info("Database: Supabase PostgreSQL")
else:
    # Fallback to SQLite for local dev
    _db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sos_local.db")
    _url = f"sqlite+aiosqlite:///{_db_path}"
    logger.info("Database: Local SQLite at %s", _db_path)

# SQLite needs connect_args for async
_connect_args = {"check_same_thread": False} if "sqlite" in _url else {}

engine = create_async_engine(_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def init_db():
    """Create all tables — call once at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")


async def get_db():
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def reset_engine():
    """Dispose engine and clear state. Used for testing."""
    global engine, AsyncSessionLocal
    await engine.dispose()
    logger.info("Database engine disposed")
