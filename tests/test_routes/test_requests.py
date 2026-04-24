import pytest
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app
from app import settings as settings_module
from app.services.library_sync import sync_library


@pytest.fixture
async def seeded_client(db_path, tmp_path, monkeypatch):
    """Client with two seeded books in a series."""
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)

    from app.services import library_sync

    items = [
        {
            "abs_id": "abs-001",
            "abs_url": "http://abs.local/item/abs-001",
            "title": "The Way of Kings",
            "author": "Brandon Sanderson",
            "series_items": [{"name": "The Stormlight Archive", "sequence": "1"}],
            "cover_url": "",
            "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}],
        },
    ]

    async def mock_list(self):
        return items

    monkeypatch.setattr(
        "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
        mock_list,
    )

    async def no_hc_link(*a, **kw):
        return False

    monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "k", "library_id": []}})
        await sync_library()
        yield c


class TestDeleteRequest:
    async def test_delete_unknown_returns_404(self, seeded_client):
        resp = await seeded_client.delete(f"/api/requests/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_delete_request_succeeds(self, seeded_client):
        books = (await seeded_client.get("/api/books")).json()["items"]
        book_id = books[0]["id"]
        req = (await seeded_client.post("/api/requests", json={"book_id": book_id, "type": "ebook"})).json()
        resp = await seeded_client.delete(f"/api/requests/{req['id']}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_delete_removes_book_series_when_no_formats(self, seeded_client):
        """Deleting the last request for a format-less book should remove its book_series row."""
        from app.database import get_db

        books = (await seeded_client.get("/api/books")).json()["items"]
        book_id = books[0]["id"]

        # Remove formats so the book looks like a request-only entry
        async with get_db() as db:
            await db.execute("DELETE FROM book_formats WHERE book_id = ?", (book_id,))
            await db.commit()

        req = (await seeded_client.post("/api/requests", json={"book_id": book_id, "type": "ebook"})).json()

        # book_series row should exist at this point
        async with get_db() as db:
            row = await (await db.execute("SELECT 1 FROM book_series WHERE book_id = ?", (book_id,))).fetchone()
        assert row is not None

        await seeded_client.delete(f"/api/requests/{req['id']}")

        # book_series row should be gone now
        async with get_db() as db:
            row = await (await db.execute("SELECT 1 FROM book_series WHERE book_id = ?", (book_id,))).fetchone()
        assert row is None

    async def test_delete_preserves_book_series_when_formats_exist(self, seeded_client):
        """Deleting a request for a book that has formats should NOT remove its book_series row."""
        from app.database import get_db

        books = (await seeded_client.get("/api/books")).json()["items"]
        book_id = books[0]["id"]

        # Book still has formats from the seed
        req = (await seeded_client.post("/api/requests", json={"book_id": book_id, "type": "ebook"})).json()
        await seeded_client.delete(f"/api/requests/{req['id']}")

        async with get_db() as db:
            row = await (await db.execute("SELECT 1 FROM book_series WHERE book_id = ?", (book_id,))).fetchone()
        assert row is not None

    async def test_delete_preserves_book_series_when_other_requests_remain(self, seeded_client):
        """Deleting one request should not clean up book_series if other requests still exist."""
        from app.database import get_db

        books = (await seeded_client.get("/api/books")).json()["items"]
        book_id = books[0]["id"]

        # Remove formats so the book is request-only
        async with get_db() as db:
            await db.execute("DELETE FROM book_formats WHERE book_id = ?", (book_id,))
            await db.commit()

        req_ebook = (await seeded_client.post("/api/requests", json={"book_id": book_id, "type": "ebook"})).json()
        req_audio = (await seeded_client.post("/api/requests", json={"book_id": book_id, "type": "audiobook"})).json()

        # Delete only the ebook request — audiobook still pending
        await seeded_client.delete(f"/api/requests/{req_ebook['id']}")

        async with get_db() as db:
            row = await (await db.execute("SELECT 1 FROM book_series WHERE book_id = ?", (book_id,))).fetchone()
        assert row is not None
