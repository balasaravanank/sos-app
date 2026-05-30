import pytest
import pytest_asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from httpx import AsyncClient, ASGITransport

# Force all tests to use asyncio
pytestmark = pytest.mark.asyncio

# Shared test IDs
test_user_id = str(uuid.uuid4())
test_sos_id = str(uuid.uuid4())

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _init_database():
    """Reset engine so it binds to this session event loop, then init DB."""
    from app.db import reset_engine
    await reset_engine()
    from app.init_db import init_db
    await init_db()
    await reset_engine()
    yield
    await reset_engine()

@pytest_asyncio.fixture(autouse=True)
async def reset_engine_per_test():
    """Reset the database engine before and after each test function.
    This ensures that each test's event loop gets a fresh engine bound to its loop context,
    preventing 'Future attached to a different loop' errors.
    """
    from app.db import reset_engine
    await reset_engine()
    yield
    await reset_engine()

@pytest_asyncio.fixture
async def client(_init_database):
    """Provide an httpx AsyncClient wired to the FastAPI app."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ──────────────────────────────────────
# TESTS
# ──────────────────────────────────────

async def test_location_update_valid(client):
    payload = {
        "user_id": test_user_id,
        "sos_id": test_sos_id,
        "lat": 13.0827,
        "lng": 80.2707,
        "accuracy": 10.5
    }
    response = await client.post("/api/location/update", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["recorded"] is True

async def test_location_update_without_sos_id(client):
    payload = {
        "user_id": test_user_id,
        "lat": 13.0827,
        "lng": 80.2707,
        "accuracy": 10.5
    }
    response = await client.post("/api/location/update", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["recorded"] is True

async def test_location_update_invalid_lat(client):
    payload = {
        "user_id": test_user_id,
        "sos_id": test_sos_id,
        "lat": 95.0,
        "lng": 80.2707,
        "accuracy": 10.5
    }
    response = await client.post("/api/location/update", json=payload)
    assert response.status_code == 422

async def test_location_update_invalid_accuracy(client):
    payload = {
        "user_id": test_user_id,
        "sos_id": test_sos_id,
        "lat": 13.0827,
        "lng": 80.2707,
        "accuracy": 600.0
    }
    response = await client.post("/api/location/update", json=payload)
    assert response.status_code == 422

async def test_stop_location_stream(client):
    payload = {
        "user_id": test_user_id,
        "sos_id": test_sos_id
    }
    response = await client.post("/api/location/stop", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["stopped"] is True

async def test_cached_location_redis_fallback(client):
    response = await client.get(f"/api/location/cached?user_id={test_user_id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "lat" in data["data"]
    assert "lng" in data["data"]

async def test_emergency_contacts(client):
    response = await client.get("/api/cache/emergency-contacts")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert "contacts" in data["data"]
    assert len(data["data"]["contacts"]) >= 4

async def test_rate_limit_exceeded(client):
    from app.redis import get_redis
    redis = get_redis()
    rl_user_id = str(uuid.uuid4())
    
    # Seed the rate limit counter to 60 directly in Redis
    key = f"rate:user:{rl_user_id}"
    await redis.set(key, "60", ex=60)
    
    payload = {
        "user_id": rl_user_id,
        "lat": 13.0827,
        "lng": 80.2707,
        "accuracy": 10.5
    }
    
    # This request will be the 61st, thus rate limited
    response = await client.post("/api/location/update", json=payload)
    assert response.status_code == 429
