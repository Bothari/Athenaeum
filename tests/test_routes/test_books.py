import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app import settings as settings_module
from app.services.library_sync import sync_library


@pytest.fixture
async def client(db_path, tmp_path, monkeypatch):
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def seeded_client(db_path, tmp_path, monkeypatch):
    """Client with two books, one author, one series already synced."""
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
            "cover_url": "http://cover/1",
            "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}],
        },
        {
            "abs_id": "abs-002",
            "abs_url": "http://abs.local/item/abs-002",
            "title": "Words of Radiance",
            "author": "Brandon Sanderson",
            "series_items": [{"name": "The Stormlight Archive", "sequence": "2"}],
            "cover_url": "http://cover/2",
            "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}],
        },
    ]

    async def mock_list(self):
        return items

    monkeypatch.setattr(
        "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
        mock_list,
    )
    async def no_hc_link(*a, **kw): return False
    monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "k", "library_id": []}})
        await sync_library()
        yield c


class TestListBooks:
    async def test_empty(self, client):
        resp = await client.get("/api/books")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 50
        assert data["offset"] == 0

    async def test_returns_books(self, seeded_client):
        resp = await seeded_client.get("/api/books")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_book_shape(self, seeded_client):
        resp = await seeded_client.get("/api/books")
        book = resp.json()["items"][0]
        assert "id" in book
        assert "title" in book
        assert "authors" in book
        assert "series" in book
        assert "link" in book
        assert isinstance(book["authors"], list)
        assert book["authors"][0]["name"] == "Brandon Sanderson"

    async def test_filter_by_title(self, seeded_client):
        resp = await seeded_client.get("/api/books?q=Way+of+Kings")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "The Way of Kings"

    async def test_filter_by_author(self, seeded_client):
        resp = await seeded_client.get("/api/books?q=Sanderson")
        data = resp.json()
        assert data["total"] == 2

    async def test_pagination(self, seeded_client):
        resp = await seeded_client.get("/api/books?limit=1&offset=0")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["total"] == 2

        resp2 = await seeded_client.get("/api/books?limit=1&offset=1")
        data2 = resp2.json()
        assert len(data2["items"]) == 1
        assert data2["items"][0]["id"] != data["items"][0]["id"]

    async def test_sort_title_asc(self, seeded_client):
        resp = await seeded_client.get("/api/books?sort=title&dir=asc")
        titles = [b["title"] for b in resp.json()["items"]]
        assert titles == sorted(titles, key=str.lower)

    async def test_sort_title_desc(self, seeded_client):
        resp = await seeded_client.get("/api/books?sort=title&dir=desc")
        titles = [b["title"] for b in resp.json()["items"]]
        assert titles == sorted(titles, key=str.lower, reverse=True)


class TestGetBook:
    async def test_returns_book(self, seeded_client):
        books = (await seeded_client.get("/api/books")).json()["items"]
        book_id = books[0]["id"]
        resp = await seeded_client.get(f"/api/books/{book_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == book_id
        assert "requests" in resp.json()

    async def test_404_on_unknown(self, client):
        resp = await client.get("/api/books/nonexistent-id")
        assert resp.status_code == 404


class TestListAuthors:
    async def test_empty(self, client):
        resp = await client.get("/api/authors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_returns_authors(self, seeded_client):
        resp = await seeded_client.get("/api/authors")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Brandon Sanderson"

    async def test_author_shape(self, seeded_client):
        resp = await seeded_client.get("/api/authors")
        author = resp.json()["items"][0]
        assert "id" in author
        assert "name" in author
        assert "book_count" in author
        assert "link" in author
        assert author["book_count"] == 2

    async def test_filter_by_name(self, seeded_client):
        resp = await seeded_client.get("/api/authors?q=Sanderson")
        assert resp.json()["total"] == 1

        resp2 = await seeded_client.get("/api/authors?q=nobody")
        assert resp2.json()["total"] == 0

    async def test_pagination(self, seeded_client):
        resp = await seeded_client.get("/api/authors?limit=1&offset=0")
        assert len(resp.json()["items"]) == 1


class TestGetAuthorBooks:
    async def test_returns_books(self, seeded_client):
        authors = (await seeded_client.get("/api/authors")).json()["items"]
        author_id = authors[0]["id"]
        resp = await seeded_client.get(f"/api/authors/{author_id}/books")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_404_on_unknown(self, client):
        resp = await client.get("/api/authors/nonexistent/books")
        assert resp.status_code == 404


class TestListSeries:
    async def test_empty(self, client):
        resp = await client.get("/api/series")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_returns_series(self, seeded_client):
        resp = await seeded_client.get("/api/series")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "The Stormlight Archive"

    async def test_series_shape(self, seeded_client):
        resp = await seeded_client.get("/api/series")
        s = resp.json()["items"][0]
        assert "id" in s
        assert "name" in s
        assert "book_count" in s
        assert "link" in s
        assert s["book_count"] == 2

    async def test_filter_by_name(self, seeded_client):
        resp = await seeded_client.get("/api/series?q=Stormlight")
        assert resp.json()["total"] == 1

        resp2 = await seeded_client.get("/api/series?q=nobody")
        assert resp2.json()["total"] == 0

    async def test_pagination(self, seeded_client):
        resp = await seeded_client.get("/api/series?limit=1&offset=0")
        assert len(resp.json()["items"]) == 1


class TestGetSeriesBooks:
    async def test_returns_books(self, seeded_client):
        series = (await seeded_client.get("/api/series")).json()["items"]
        series_id = series[0]["id"]
        resp = await seeded_client.get(f"/api/series/{series_id}/books")
        assert resp.status_code == 200
        books = resp.json()
        assert len(books) == 2
        assert all("series_position" in b for b in books)

    async def test_404_on_unknown(self, client):
        resp = await client.get("/api/series/nonexistent/books")
        assert resp.status_code == 404


class TestGetSeriesMissing:
    async def test_404_on_unknown_series(self, client):
        resp = await client.get("/api/series/nonexistent/missing")
        assert resp.status_code == 404

    async def test_no_hc_link_returns_error(self, seeded_client):
        """Series without a Hardcover link returns empty with error message."""
        series = (await seeded_client.get("/api/series")).json()["items"]
        series_id = series[0]["id"]
        resp = await seeded_client.get(f"/api/series/{series_id}/missing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert "error" in data

    async def test_missing_books_excludes_owned(self, seeded_client, monkeypatch):
        """Missing books list excludes positions already in library."""
        import app.routes.books as books_module
        from app.database import get_db

        # Set HC api key via settings API so the endpoint doesn't short-circuit
        await seeded_client.put("/api/settings", json={
            "audiobookshelf": {"url": "http://abs.local", "api_key": "k", "library_id": []},
            "hardcover": {"api_key": "test-key"},
        })

        series = (await seeded_client.get("/api/series")).json()["items"]
        series_id = series[0]["id"]
        async with get_db() as db:
            await db.execute(
                "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ?",
                ("999", series_id),
            )
            await db.commit()

        hc_books = [
            {"title": "The Way of Kings", "position": "1", "compilation": False, "hc_book_id": "", "slug": ""},
            {"title": "Words of Radiance", "position": "2", "compilation": False, "hc_book_id": "", "slug": ""},
            {"title": "Oathbringer", "position": "3", "compilation": False, "hc_book_id": "", "slug": ""},
            {"title": "Rhythm of War", "position": "4", "compilation": False, "hc_book_id": "", "slug": ""},
        ]

        async def mock_hc_series(hc_series_id, api_key):
            return hc_books

        async def mock_search(query, api_key, pages=1, context_hc_series_id=""):
            return [{"title": query, "author": "Brandon Sanderson", "author_id": "",
                     "authors": [], "subtitle": "", "narrator": "", "description": "",
                     "cover_url": "", "isbn": "", "asin": "", "pages": None,
                     "publisher": "", "published_year": None, "language": "",
                     "genres": [], "rating": None, "rating_count": 0, "users_count": 100,
                     "series": [], "is_compilation": False, "compilation_details": "",
                     "metadata_source": "hardcover", "metadata_id": f"hc-{query[:5]}",
                     "slug": "", "metadata_url": "", "hardcover_url": "",
                     "book_id": None, "in_library": False, "library_formats": [],
                     "existing_requests": [], "abs_links": []}]

        monkeypatch.setattr(books_module._book_search, "get_hc_series_books", mock_hc_series)
        monkeypatch.setattr(books_module._book_search, "search_books", mock_search)

        resp = await seeded_client.get(f"/api/series/{series_id}/missing")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" not in data
        assert data["truncated"] is False
        # positions 1 and 2 owned, so only 3 and 4 are missing
        assert len(data["items"]) == 2
        titles = [i["title"] for i in data["items"]]
        assert "Oathbringer" in titles
        assert "Rhythm of War" in titles

    async def test_compilations_excluded(self, seeded_client, monkeypatch):
        """Compilation entries are not returned as missing books."""
        import app.routes.books as books_module
        from app.database import get_db

        await seeded_client.put("/api/settings", json={
            "audiobookshelf": {"url": "http://abs.local", "api_key": "k", "library_id": []},
            "hardcover": {"api_key": "test-key"},
        })

        series = (await seeded_client.get("/api/series")).json()["items"]
        series_id = series[0]["id"]
        async with get_db() as db:
            await db.execute(
                "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ?",
                ("888", series_id),
            )
            await db.commit()

        hc_books = [
            {"title": "Stormlight 1-2 Boxset", "position": "1-2", "compilation": True, "hc_book_id": "", "slug": ""},
            {"title": "Oathbringer", "position": "3", "compilation": False, "hc_book_id": "", "slug": ""},
        ]

        async def mock_hc_series(hc_series_id, api_key):
            return hc_books

        async def mock_search(query, api_key, pages=1, context_hc_series_id=""):
            return [{"title": query, "author": "", "author_id": "", "authors": [],
                     "subtitle": "", "narrator": "", "description": "", "cover_url": "",
                     "isbn": "", "asin": "", "pages": None, "publisher": "",
                     "published_year": None, "language": "", "genres": [],
                     "rating": None, "rating_count": 0, "users_count": 10,
                     "series": [], "is_compilation": False, "compilation_details": "",
                     "metadata_source": "hardcover", "metadata_id": "hc-oathbringer",
                     "slug": "", "metadata_url": "", "hardcover_url": "",
                     "book_id": None, "in_library": False, "library_formats": [],
                     "existing_requests": [], "abs_links": []}]

        monkeypatch.setattr(books_module._book_search, "get_hc_series_books", mock_hc_series)
        monkeypatch.setattr(books_module._book_search, "search_books", mock_search)

        resp = await seeded_client.get(f"/api/series/{series_id}/missing")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" not in data
        # Only Oathbringer (non-compilation, not owned by position); boxset excluded
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Oathbringer"

    async def test_hc_api_failure_returns_empty(self, seeded_client, monkeypatch):
        """If HC API call fails, returns empty items without crashing."""
        import app.routes.books as books_module
        from app.database import get_db

        await seeded_client.put("/api/settings", json={
            "audiobookshelf": {"url": "http://abs.local", "api_key": "k", "library_id": []},
            "hardcover": {"api_key": "test-key"},
        })

        series = (await seeded_client.get("/api/series")).json()["items"]
        series_id = series[0]["id"]
        async with get_db() as db:
            await db.execute(
                "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ?",
                ("777", series_id),
            )
            await db.commit()

        async def mock_hc_series(hc_series_id, api_key):
            return []

        monkeypatch.setattr(books_module._book_search, "get_hc_series_books", mock_hc_series)

        resp = await seeded_client.get(f"/api/series/{series_id}/missing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["truncated"] is False
