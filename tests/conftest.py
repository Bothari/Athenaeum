import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture
async def db_path(tmp_path, monkeypatch):
    """Temporary isolated SQLite DB with migrations applied."""
    path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.database.DB_PATH", path)
    async with aiosqlite.connect(path) as db:
        from app.database import _run_migrations
        await _run_migrations(db)
    yield path


@pytest_asyncio.fixture
async def client(db_path):
    """ASGI test client wired to the isolated test DB."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
