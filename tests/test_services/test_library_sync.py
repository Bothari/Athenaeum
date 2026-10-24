import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.library_sync import _split_authors, _get_or_create_author, _get_or_create_series, sync_library
from app import settings as settings_module


# ── _split_authors ─────────────────────────────────────────────────────────────

class TestSplitAuthors:
    def test_single_author(self):
        assert _split_authors("Brandon Sanderson") == ["Brandon Sanderson"]

    def test_comma_split(self):
        assert _split_authors("Terry Pratchett, Neil Gaiman") == ["Terry Pratchett", "Neil Gaiman"]

    def test_ampersand_split(self):
        assert _split_authors("Terry Pratchett & Neil Gaiman") == ["Terry Pratchett", "Neil Gaiman"]

    def test_and_split(self):
        assert _split_authors("Brandon Sanderson and Janci Patterson") == ["Brandon Sanderson", "Janci Patterson"]

    def test_semicolon_split(self):
        assert _split_authors("Author One; Author Two") == ["Author One", "Author Two"]

    def test_strips_translator_annotation(self):
        result = _split_authors("Fyodor Dostoevsky, Richard Pevear (translator)")
        assert "Richard Pevear" in result
        assert not any("translator" in a for a in result)

    def test_preserves_original_casing(self):
        result = _split_authors("Brandon Sanderson AND Janci Patterson")
        assert "Brandon Sanderson" in result
        assert "Janci Patterson" in result

    def test_empty_string(self):
        assert _split_authors("") == []

    def test_none_like_empty(self):
        assert _split_authors(None) == []


# ── _get_or_create_author ──────────────────────────────────────────────────────

class TestGetOrCreateAuthor:
    async def test_creates_new_author(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            author_id = await _get_or_create_author(db, "Test Author")
            await db.commit()
            row = await (await db.execute("SELECT name FROM authors WHERE id = ?", (author_id,))).fetchone()
            assert row["name"] == "Test Author"

    async def test_returns_existing_author(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            id1 = await _get_or_create_author(db, "Same Author")
            await db.commit()
            id2 = await _get_or_create_author(db, "same author")
            await db.commit()
            assert id1 == id2

    async def test_creates_author_links_row(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            author_id = await _get_or_create_author(db, "Linked Author")
            await db.commit()
            link = await (await db.execute(
                "SELECT author_id FROM author_links WHERE author_id = ?", (author_id,)
            )).fetchone()
            assert link is not None

    async def test_idempotent_link_row(self, db_path):
        """Calling twice must not create duplicate author_links rows."""
        from app.database import get_db
        async with get_db() as db:
            author_id = await _get_or_create_author(db, "Idempotent Author")
            await db.commit()
            await _get_or_create_author(db, "Idempotent Author")
            await db.commit()
            rows = await (await db.execute(
                "SELECT COUNT(*) FROM author_links WHERE author_id = ?", (author_id,)
            )).fetchone()
            assert rows[0] == 1


# ── _get_or_create_series ──────────────────────────────────────────────────────

class TestGetOrCreateSeries:
    async def test_creates_new_series(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            series_id = await _get_or_create_series(db, "The Stormlight Archive")
            await db.commit()
            row = await (await db.execute("SELECT name FROM series WHERE id = ?", (series_id,))).fetchone()
            assert row["name"] == "The Stormlight Archive"

    async def test_returns_existing_series(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            id1 = await _get_or_create_series(db, "Mistborn")
            await db.commit()
            id2 = await _get_or_create_series(db, "mistborn")
            await db.commit()
            assert id1 == id2

    async def test_idempotent_series_links_row(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            series_id = await _get_or_create_series(db, "Idempotent Series")
            await db.commit()
            await _get_or_create_series(db, "Idempotent Series")
            await db.commit()
            rows = await (await db.execute(
                "SELECT COUNT(*) FROM series_links WHERE series_id = ?", (series_id,)
            )).fetchone()
            assert rows[0] == 1


# ── sync_library ───────────────────────────────────────────────────────────────

ABS_ITEMS = [
    {
        "abs_id": "abs-001",
        "abs_url": "http://abs.local/item/abs-001",
        "title": "The Way of Kings",
        "author": "Brandon Sanderson",
        "series_items": [{"name": "The Stormlight Archive", "sequence": "1"}],
        "cover_url": "http://abs.local/cover/abs-001",
        "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}],
    },
    {
        "abs_id": "abs-002",
        "abs_url": "http://abs.local/item/abs-002",
        "title": "Words of Radiance",
        "author": "Brandon Sanderson",
        "series_items": [{"name": "The Stormlight Archive", "sequence": "2"}],
        "cover_url": "http://abs.local/cover/abs-002",
        "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}, {"type": "ebook"}],
    },
]


@pytest.fixture
async def sync_client(db_path, tmp_path, monkeypatch):
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestSyncLibrary:
    async def test_inserts_books_authors_series(self, sync_client, monkeypatch):
        from app.services import library_sync
        async def mock_list_all_items(self):
            return ABS_ITEMS
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})
        result = await sync_library()

        assert result["created"] == 2
        assert result["errors"] == 0

        from app.database import get_db
        async with get_db() as db:
            book_count = (await (await db.execute("SELECT COUNT(*) FROM books")).fetchone())[0]
            author_count = (await (await db.execute("SELECT COUNT(*) FROM authors")).fetchone())[0]
            series_count = (await (await db.execute("SELECT COUNT(*) FROM series")).fetchone())[0]

        assert book_count == 2
        assert author_count == 1  # Brandon Sanderson appears in both — only created once
        assert series_count == 1  # Same series

    async def test_resync_does_not_duplicate(self, sync_client, monkeypatch):
        from app.services import library_sync
        async def mock_list_all_items(self):
            return ABS_ITEMS[:1]
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})

        await sync_library()
        await sync_library()  # Second run

        from app.database import get_db
        async with get_db() as db:
            book_count = (await (await db.execute("SELECT COUNT(*) FROM books")).fetchone())[0]
            author_count = (await (await db.execute("SELECT COUNT(*) FROM authors")).fetchone())[0]
            link_count = (await (await db.execute("SELECT COUNT(*) FROM book_links")).fetchone())[0]

        assert book_count == 1
        assert author_count == 1
        assert link_count == 1

    async def test_in_library_formats_created(self, sync_client, monkeypatch):
        from app.services import library_sync
        async def mock_list_all_items(self):
            return ABS_ITEMS[1:2]  # Words of Radiance — has audiobook + ebook
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})
        await sync_library()

        from app.database import get_db
        async with get_db() as db:
            rows = await (await db.execute(
                "SELECT type FROM book_formats"
            )).fetchall()

        types = {r["type"] for r in rows}
        assert "audiobook" in types
        assert "ebook" in types

    async def test_author_links_not_duplicated_on_resync(self, sync_client, monkeypatch):
        """author_links must use INSERT OR IGNORE, never INSERT OR REPLACE."""
        from app.services import library_sync
        async def mock_list_all_items(self):
            return ABS_ITEMS[:1]
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})
        await sync_library()
        await sync_library()

        from app.database import get_db
        async with get_db() as db:
            count = (await (await db.execute("SELECT COUNT(*) FROM author_links")).fetchone())[0]
        assert count == 1

    async def test_series_links_not_duplicated_on_resync(self, sync_client, monkeypatch):
        """series_links must use INSERT OR IGNORE, never INSERT OR REPLACE."""
        from app.services import library_sync
        async def mock_list_all_items(self):
            return ABS_ITEMS[:1]
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})
        await sync_library()
        await sync_library()

        from app.database import get_db
        async with get_db() as db:
            count = (await (await db.execute("SELECT COUNT(*) FROM series_links")).fetchone())[0]
        assert count == 1

    async def test_new_format_added_on_resync(self, sync_client, monkeypatch):
        """If a new format appears on resync, it is added to book_formats."""
        from app.services import library_sync

        audiobook_only = [{**ABS_ITEMS[0], "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}]}]
        audiobook_and_ebook = [{**ABS_ITEMS[0], "formats": [{"type": "audiobook", "narrator": "Michael Kramer"}, {"type": "ebook"}]}]

        call_count = 0
        async def mock_list_all_items(self):
            nonlocal call_count
            call_count += 1
            return audiobook_only if call_count == 1 else audiobook_and_ebook

        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)

        await sync_client.put("/api/settings", json={"audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}})
        await sync_library()
        await sync_library()

        from app.database import get_db
        async with get_db() as db:
            rows = await (await db.execute(
                "SELECT type FROM book_formats"
            )).fetchall()
        types = {r["type"] for r in rows}
        assert "audiobook" in types
        assert "ebook" in types


# ── Items ABS reports as missing ───────────────────────────────────────────────

MISSING_ITEM = {
    "abs_id": "abs-gone",
    "abs_url": "http://abs.local/item/abs-gone",
    "title": "A Deleted Book",
    "author": "Ann Author",
    "series_items": [],
    "cover_url": None,
    "formats": [{"type": "ebook", "narrator": ""}],
    "is_missing": True,
}


class TestMissingAbsItems:
    """ABS flags an item whose files have gone rather than deleting it, so a book
    deleted in Athenaeum stayed in ABS's item list forever and sync kept bringing
    it back with a new id (ath-b9k.9). Observed twice with the same title.
    """

    async def _sync_with(self, sync_client, monkeypatch, items):
        from app.services import library_sync

        async def mock_list_all_items(self):
            return items
        monkeypatch.setattr(
            "app.services.audiobookshelf.AudiobookshelfService.list_all_items",
            mock_list_all_items,
        )
        async def no_hc_link(*a, **kw): return False
        monkeypatch.setattr(library_sync, "_link_to_hardcover", no_hc_link)
        await sync_client.put("/api/settings", json={
            "audiobookshelf": {"url": "http://abs.local", "api_key": "key", "library_id": []}
        })
        return await sync_library()

    async def test_a_missing_item_is_not_created(self, sync_client, monkeypatch):
        result = await self._sync_with(sync_client, monkeypatch, [MISSING_ITEM])
        assert result["created"] == 0, result
        from app.database import get_db
        async with get_db() as db:
            row = await (await db.execute(
                "SELECT 1 FROM books WHERE title='A Deleted Book'")).fetchone()
        assert row is None, "sync recreated a book ABS says is missing"

    async def test_a_missing_item_does_not_block_the_rest(self, sync_client, monkeypatch):
        result = await self._sync_with(sync_client, monkeypatch, [MISSING_ITEM] + ABS_ITEMS)
        assert result["created"] == 2, result

    async def test_an_already_linked_item_is_still_synced_when_missing(
        self, sync_client, monkeypatch
    ):
        """A temporarily unmounted drive also reports missing, so an item we already
        hold must not be treated as deleted."""
        from app.database import get_db

        # first sync while present, so the book and its link exist
        present = dict(MISSING_ITEM, is_missing=False)
        await self._sync_with(sync_client, monkeypatch, [present])
        async with get_db() as db:
            before = await (await db.execute(
                "SELECT book_id FROM book_links WHERE abs_id='abs-gone'")).fetchone()
        assert before is not None

        # now it reports missing; the existing book must survive untouched
        await self._sync_with(sync_client, monkeypatch, [MISSING_ITEM])
        async with get_db() as db:
            after = await (await db.execute(
                "SELECT book_id FROM book_links WHERE abs_id='abs-gone'")).fetchone()
            book = await (await db.execute(
                "SELECT 1 FROM books WHERE title='A Deleted Book'")).fetchone()
        assert after is not None and after["book_id"] == before["book_id"]
        assert book is not None, "an unmounted drive must not look like a deletion"
