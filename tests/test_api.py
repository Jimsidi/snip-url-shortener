import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import os

os.environ["DB_PATH"] = ":memory:"

import app.database as db_module
from app.main import app
from app.database import init_db


@pytest_asyncio.fixture
async def client():
    # Reset and init DB fresh for each test
    if db_module._shared_conn:
        await db_module._shared_conn.close()
    db_module._shared_conn = None
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # Cleanup
    if db_module._shared_conn:
        await db_module._shared_conn.close()
    db_module._shared_conn = None


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_shorten_url(client):
    r = await client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 200
    data = r.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 6


@pytest.mark.asyncio
async def test_custom_code(client):
    r = await client.post("/api/shorten", json={"url": "https://google.com", "custom_code": "goog"})
    assert r.status_code == 200
    assert r.json()["short_code"] == "goog"


@pytest.mark.asyncio
async def test_duplicate_custom_code(client):
    await client.post("/api/shorten", json={"url": "https://google.com", "custom_code": "dup"})
    r = await client.post("/api/shorten", json={"url": "https://bing.com", "custom_code": "dup"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_redirect(client):
    r = await client.post("/api/shorten", json={"url": "https://example.com", "custom_code": "exm"})
    assert r.status_code == 200
    r2 = await client.get("/exm", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_stats(client):
    await client.post("/api/shorten", json={"url": "https://example.com", "custom_code": "stt"})
    await client.get("/stt", follow_redirects=False)
    r = await client.get("/api/stats/stt")
    assert r.status_code == 200
    assert r.json()["clicks"] == 1


@pytest.mark.asyncio
async def test_not_found(client):
    r = await client.get("/doesnotexist", follow_redirects=False)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_custom_code_too_short(client):
    r = await client.post("/api/shorten", json={"url": "https://x.com", "custom_code": "ab"})
    assert r.status_code == 400