import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app
from app import settings as settings_module
from app.auth import _make_session_token
from app.services.library_sync import sync_library

SECRET = "test-session-secret"
DAYS = 30


def _token(user_id: str, role: str) -> str:
    return _make_session_token(user_id, role, SECRET, DAYS)


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


# ── Issue #4: status filter dropped the non-admin ownership condition ────────────

class TestListRequestsStatusFilter:
    """`list_requests` built its WHERE clause by REPLACING `conditions` when a status
    filter was given, which discarded the non-admin ownership condition while leaving
    its binding in `bind`. For a non-admin that meant 1 placeholder against 2 bindings
    — sqlite3.ProgrammingError, HTTP 500 — and, had the counts ever lined up, a
    non-admin would have seen every user's requests. Admins never hit it (their bind
    list is empty), which is why it went unnoticed.
    """

    @pytest_asyncio.fixture
    async def req_client(self, db_path, tmp_path, monkeypatch):
        settings_path = str(tmp_path / "settings.yaml")
        monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            await c.put("/api/settings", json={
                "auth": {"form_enabled": True, "session_secret": SECRET, "session_days": DAYS}
            })
            await self._seed()
            yield c

    @staticmethod
    async def _seed():
        """One book, plus a failed + a pending request for each of two users."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT INTO books (id, title, created_at, updated_at) "
                "VALUES ('bk1', 'A Book', '2026-01-01', '2026-01-01')")
            for uid in ("user-a", "user-b"):
                # requests.requested_by_user_id REFERENCES users(id)
                await db.execute(
                    "INSERT INTO users (id, username, role, created_at, updated_at) "
                    "VALUES (?, ?, 'user', '2026-01-01', '2026-01-01')", (uid, uid))
                for st in ("failed", "pending"):
                    await db.execute(
                        "INSERT INTO requests (id, book_id, type, status, "
                        "requested_by_user_id, created_at, updated_at) "
                        "VALUES (?, 'bk1', 'ebook', ?, ?, '2026-01-01', '2026-01-01')",
                        (f"{uid}-{st}", st, uid))
            await db.commit()

    async def test_non_admin_status_filter_does_not_500(self, req_client):
        """The reported crash: GET /api/requests?status=failed as a non-admin."""
        resp = await req_client.get("/api/requests?status=failed&limit=1",
                                    cookies={"session": _token("user-a", "user")})
        assert resp.status_code == 200, resp.text

    async def test_non_admin_status_filter_still_scopes_to_own_requests(self, req_client):
        """The security half: filtering by status must not widen visibility."""
        resp = await req_client.get("/api/requests?status=failed",
                                    cookies={"session": _token("user-a", "user")})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert [i["id"] for i in items] == ["user-a-failed"]
        assert all(i["requested_by_user_id"] == "user-a" for i in items)

    async def test_admin_status_filter_sees_all(self, req_client):
        resp = await req_client.get("/api/requests?status=failed",
                                    cookies={"session": _token("admin-1", "admin")})
        assert resp.status_code == 200
        assert {i["id"] for i in resp.json()["items"]} == {"user-a-failed", "user-b-failed"}

    async def test_explicit_in_library_status_is_still_selectable(self, req_client):
        """The replacement also dropped the default `status != 'in_library'` exclusion,
        which is why it could not simply become an append: an explicit
        ?status=in_library must still return those rows."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT INTO requests (id, book_id, type, status, requested_by_user_id, "
                "created_at, updated_at) VALUES "
                "('lib-1', 'bk1', 'ebook', 'in_library', 'user-a', '2026-01-01', '2026-01-01')")
            await db.commit()
        resp = await req_client.get("/api/requests?status=in_library",
                                    cookies={"session": _token("user-a", "user")})
        assert resp.status_code == 200
        assert [i["id"] for i in resp.json()["items"]] == ["lib-1"]

    async def test_in_library_hidden_by_default(self, req_client):
        """...while remaining hidden when no status filter is given."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT INTO requests (id, book_id, type, status, requested_by_user_id, "
                "created_at, updated_at) VALUES "
                "('lib-2', 'bk1', 'ebook', 'in_library', 'user-a', '2026-01-01', '2026-01-01')")
            await db.commit()
        resp = await req_client.get("/api/requests",
                                    cookies={"session": _token("user-a", "user")})
        assert resp.status_code == 200
        assert "lib-2" not in {i["id"] for i in resp.json()["items"]}
