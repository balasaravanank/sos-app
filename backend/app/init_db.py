import asyncio
from sqlalchemy import text
from app.db import get_engine

async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        # Enable PostGIS
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # Create location_history table
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS location_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            sos_id UUID,
            latitude NUMERIC(10,7) NOT NULL,
            longitude NUMERIC(10,7) NOT NULL,
            accuracy FLOAT,
            source VARCHAR(20) DEFAULT 'gps',
            geom geography(Point,4326),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """))
        
        # Create GIST index
        await conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_location_geom
        ON location_history
        USING GIST(geom);
        """))

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized successfully.")
