"""Deleting one format of a book, and optionally its files.

Cancelling a request was the only way to remove a book, and the control is
disabled once the request is fulfilled — so a book in the library could not be
removed at all. These cover the delete pair, and especially the cases where it
must refuse to delete rather than guess.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
import yaml

NOW = datetime.now(timezone.utc).isoformat()


@pytest_asyncio.fixture
async def library(db_path, tmp_path, monkeypatch):
    """A book with both formats organized on disk, plus a seeding torrent copy."""
    from app import settings as settings_module
    from app.database import get_db

    out = tmp_path / "output"
    settings_path = tmp_path / "settings.yaml"
    settings_path.write_text(yaml.safe_dump({
        "general": {
            "output_dir": str(out),
            "separate_type_dirs": True,
            "ebook_prefix": "Ebooks",
            "audiobook_prefix": "Audiobooks",
        },
    }), encoding="utf-8")
    # get_settings() re-reads the file on every call, so patching the path is enough.
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(settings_path))

    ebook_dir = out / "Ebooks" / "Ann Author" / "A Title"
    audio_dir = out / "Audiobooks" / "Ann Author" / "A Title"
    for d in (ebook_dir, audio_dir):
        d.mkdir(parents=True)
        (d / "metadata.opf").write_text("<package/>", encoding="utf-8")
    (ebook_dir / "A Title - Ann Author.epub").write_bytes(b"epub-bytes")
    (audio_dir / "A Title - Ann Author.m4b").write_bytes(b"m4b-bytes")

    # The downloader's own copy, which must survive: a torrent grab is copied
    # rather than moved, so this is what is still being seeded.
    seeding = tmp_path / "downloads" / "A.Title"
    seeding.mkdir(parents=True)
    seeding_file = seeding / "A Title - Author, Ann.epub"
    seeding_file.write_bytes(b"epub-bytes")

    async with get_db() as db:
        await db.execute("INSERT INTO books (id,title,created_at,updated_at) VALUES ('b1','A Title',?,?)", (NOW, NOW))
        await db.execute("INSERT INTO authors (id,name,created_at,updated_at) VALUES ('a1','Ann Author',?,?)", (NOW, NOW))
        await db.execute("INSERT INTO book_authors (id,book_id,author_id,author_position,created_at) VALUES ('ba1','b1','a1',0,?)", (NOW,))
        await db.execute("INSERT INTO series (id,name,created_at,updated_at) VALUES ('s1','A Series',?,?)", (NOW, NOW))
        await db.execute("INSERT INTO book_series (id,book_id,series_id,position,created_at) VALUES ('bs1','b1','s1','1',?)", (NOW,))
        for t in ("ebook", "audiobook"):
            await db.execute(
                "INSERT INTO book_formats (id,book_id,type,narrator,created_at,updated_at) VALUES (?,?,?,'',?,?)",
                (f"bf-{t}", "b1", t, NOW, NOW),
            )
        await db.commit()

    return {"out": out, "ebook_dir": ebook_dir, "audio_dir": audio_dir, "seeding": seeding_file}


class TestPreview:
    @pytest.mark.asyncio
    async def test_reports_the_files_it_would_remove(self, client, library):
        resp = await client.get("/api/books/b1/formats/ebook/files")
        assert resp.status_code == 200
        body = resp.json()
        assert body["locatable"] is True
        kinds = {Path(f["path"]).name: f["kind"] for f in body["files"]}
        assert kinds["A Title - Ann Author.epub"] == "media"
        assert kinds["metadata.opf"] == "sidecar"

    @pytest.mark.asyncio
    async def test_only_that_format(self, client, library):
        body = (await client.get("/api/books/b1/formats/audiobook/files")).json()
        names = {Path(f["path"]).name for f in body["files"]}
        assert "A Title - Ann Author.m4b" in names
        assert "A Title - Ann Author.epub" not in names

    @pytest.mark.asyncio
    async def test_not_locatable_when_the_title_no_longer_matches_disk(self, client, library):
        """The path is re-derived from the current title, and _hc_refresh_book_titles
        rewrites titles from Hardcover — so the derivation can miss."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute("UPDATE books SET title = 'A Retitled Book' WHERE id = 'b1'")
            await db.commit()
        body = (await client.get("/api/books/b1/formats/ebook/files")).json()
        assert body["locatable"] is False
        assert body["files"] == []

    @pytest.mark.asyncio
    async def test_unknown_format_rejected(self, client, library):
        assert (await client.get("/api/books/b1/formats/paperback/files")).status_code == 400

    @pytest.mark.asyncio
    async def test_absent_format_is_404(self, client, library):
        from app.database import get_db
        async with get_db() as db:
            await db.execute("DELETE FROM book_formats WHERE book_id='b1' AND type='ebook'")
            await db.commit()
        assert (await client.get("/api/books/b1/formats/ebook/files")).status_code == 404


class TestDelete:
    @pytest.mark.asyncio
    async def test_rows_go_but_files_stay_by_default(self, client, library):
        resp = await client.request("DELETE", "/api/books/b1/formats/ebook")
        assert resp.status_code == 200, resp.text
        assert resp.json()["files_removed"] == []
        assert (library["ebook_dir"] / "A Title - Ann Author.epub").exists()

        from app.database import get_db
        async with get_db() as db:
            left = await (await db.execute("SELECT type FROM book_formats WHERE book_id='b1'")).fetchall()
        assert [r["type"] for r in left] == ["audiobook"]

    @pytest.mark.asyncio
    async def test_files_go_when_asked(self, client, library):
        resp = await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["files_removed"]) == 2       # the epub and its metadata.opf
        assert body["dir_removed"] is True
        assert not library["ebook_dir"].exists()

    @pytest.mark.asyncio
    async def test_the_other_format_is_untouched(self, client, library):
        await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        assert (library["audio_dir"] / "A Title - Ann Author.m4b").exists()
        assert (library["audio_dir"] / "metadata.opf").exists()

    @pytest.mark.asyncio
    async def test_the_seeding_copy_is_never_touched(self, client, library):
        """A torrent grab is copied, not moved, so the downloader still holds the
        original. Deleting it would break the torrent and cost ratio."""
        await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        assert library["seeding"].exists(), "deleted the downloader's copy"

    @pytest.mark.asyncio
    async def test_a_directory_with_no_book_in_it_is_left_alone(self, client, library):
        """If the derivation misses, the folder may hold someone else's files or just
        our sidecar. Removing sidecars alone destroys evidence and achieves nothing."""
        (library["ebook_dir"] / "A Title - Ann Author.epub").unlink()
        resp = await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        assert resp.status_code == 200, resp.text
        assert resp.json()["files_removed"] == []
        assert (library["ebook_dir"] / "metadata.opf").exists(), "swept up a sidecar with no book"

    @pytest.mark.asyncio
    async def test_an_unexpected_file_keeps_its_directory(self, client, library):
        (library["ebook_dir"] / "notes-i-wrote.txt").write_text("mine", encoding="utf-8")
        resp = await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        assert resp.json()["dir_removed"] is False
        assert (library["ebook_dir"] / "notes-i-wrote.txt").exists()

    @pytest.mark.asyncio
    async def test_deleting_the_last_format_orphans_the_book_from_its_series(self, client, library):
        """Matches what cancelling the last request already does, so the book shows
        up as missing again rather than lingering as a phantom series entry."""
        from app.database import get_db
        await client.request("DELETE", "/api/books/b1/formats/ebook")
        assert (await client.request("DELETE", "/api/books/b1/formats/audiobook")).json()["book_orphaned"] is True
        async with get_db() as db:
            rows = await (await db.execute("SELECT 1 FROM book_series WHERE book_id='b1'")).fetchall()
        assert rows == []

    @pytest.mark.asyncio
    async def test_the_delete_is_recorded_against_the_book(self, client, library):
        """request_events has no FK and is keyed by book_id, so it outlives the
        request and the cascaded download row — see ath-b9k.1."""
        from app.database import get_db
        await client.request("DELETE", "/api/books/b1/formats/ebook?delete_files=true")
        async with get_db() as db:
            ev = await (await db.execute(
                "SELECT event_type, detail FROM request_events WHERE book_id='b1' ORDER BY created_at DESC LIMIT 1"
            )).fetchone()
        assert ev["event_type"] == "format_deleted"
        assert "ebook" in ev["detail"]

    @pytest.mark.asyncio
    async def test_unknown_book_is_404(self, client, library):
        assert (await client.request("DELETE", "/api/books/nope/formats/ebook")).status_code == 404


class TestDeleteWholeBook:
    """DELETE /books/{id} — one control, optional format subset.

    The per-format delete left the books row standing, so a book with nothing held
    and nothing requested kept its detail page with an empty shell on it. Observed
    on the dev instance: Wayward Pines ended up with 0 formats, 0 requests and 0
    series, and was still reachable.
    """

    @pytest.mark.asyncio
    async def test_deleting_everything_removes_the_entry(self, client, library):
        from app.database import get_db
        resp = await client.request("DELETE", "/api/books/b1")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["entry_deleted"] is True
        assert sorted(body["formats_deleted"]) == ["audiobook", "ebook"]

        async with get_db() as db:
            for table, col in (("books", "id"), ("book_formats", "book_id"),
                               ("book_authors", "book_id"), ("book_links", "book_id"),
                               ("book_series", "book_id")):
                rows = await (await db.execute(
                    f"SELECT 1 FROM {table} WHERE {col}='b1'")).fetchall()
                assert rows == [], f"{table} still references the deleted book"

    @pytest.mark.asyncio
    async def test_a_subset_leaves_the_book_standing(self, client, library):
        from app.database import get_db
        body = (await client.request("DELETE", "/api/books/b1?formats=ebook")).json()
        assert body["formats_deleted"] == ["ebook"]
        assert body["entry_deleted"] is False
        async with get_db() as db:
            left = await (await db.execute("SELECT type FROM book_formats WHERE book_id='b1'")).fetchall()
            book = await (await db.execute("SELECT 1 FROM books WHERE id='b1'")).fetchone()
        assert [r["type"] for r in left] == ["audiobook"]
        assert book is not None

    @pytest.mark.asyncio
    async def test_a_subset_that_empties_the_book_removes_the_entry(self, client, library):
        from app.database import get_db
        await client.request("DELETE", "/api/books/b1?formats=ebook")
        body = (await client.request("DELETE", "/api/books/b1?formats=audiobook")).json()
        assert body["entry_deleted"] is True
        async with get_db() as db:
            assert await (await db.execute("SELECT 1 FROM books WHERE id='b1'")).fetchone() is None

    @pytest.mark.asyncio
    async def test_an_already_orphaned_book_can_be_cleared(self, client, library):
        """The state the per-format delete used to leave behind, and the reason this
        endpoint treats an empty book as deletable rather than a no-op."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute("DELETE FROM book_formats WHERE book_id='b1'")
            await db.commit()
        body = (await client.request("DELETE", "/api/books/b1")).json()
        assert body["formats_deleted"] == []
        assert body["entry_deleted"] is True
        async with get_db() as db:
            assert await (await db.execute("SELECT 1 FROM books WHERE id='b1'")).fetchone() is None

    @pytest.mark.asyncio
    async def test_files_go_for_every_selected_format(self, client, library):
        resp = await client.request("DELETE", "/api/books/b1?delete_files=true")
        assert resp.status_code == 200, resp.text
        assert len(resp.json()["files_removed"]) == 4   # two media, two metadata.opf
        assert not library["ebook_dir"].exists()
        assert not library["audio_dir"].exists()

    @pytest.mark.asyncio
    async def test_the_seeding_copy_survives_a_whole_book_delete(self, client, library):
        await client.request("DELETE", "/api/books/b1?delete_files=true")
        assert library["seeding"].exists(), "deleted the downloader's copy"

    @pytest.mark.asyncio
    async def test_history_outlives_the_book(self, client, library):
        """request_events has no FK and is keyed by book_id, so the record of what
        was grabbed survives even once the book itself is gone — ath-b9k.1."""
        from app.database import get_db
        await client.request("DELETE", "/api/books/b1?delete_files=true")
        async with get_db() as db:
            events = await (await db.execute(
                "SELECT event_type FROM request_events WHERE book_id='b1'")).fetchall()
        assert any(e["event_type"] == "format_deleted" for e in events)

    @pytest.mark.asyncio
    async def test_unknown_format_in_the_subset_is_rejected(self, client, library):
        from app.database import get_db
        resp = await client.request("DELETE", "/api/books/b1?formats=ebook,paperback")
        assert resp.status_code == 400
        # and nothing was removed on the way to failing
        async with get_db() as db:
            left = await (await db.execute("SELECT type FROM book_formats WHERE book_id='b1'")).fetchall()
        assert len(left) == 2

    @pytest.mark.asyncio
    async def test_unknown_book_is_404(self, client, library):
        assert (await client.request("DELETE", "/api/books/nope")).status_code == 404


class TestRequestOnlyFormats:
    """A format can exist as a request with no book_formats row.

    Seen in production: 'Wayward Pines' had 0 formats and one ebook request still
    at in_library after the file had gone from ABS. Deriving "everything" from held
    formats alone meant deleting the book removed nothing, the request kept
    _book_is_bare false, so the entry survived — and the detail page went on showing
    an ebook, because a request at in_library renders as held.
    """

    @pytest.mark.asyncio
    async def test_deleting_the_book_clears_a_request_only_format(self, client, library):
        from app.database import get_db
        async with get_db() as db:
            await db.execute("DELETE FROM book_formats WHERE book_id='b1'")
            await db.execute(
                "INSERT INTO requests (id,book_id,type,status,created_at,updated_at)"
                " VALUES ('r-orphan','b1','ebook','in_library',?,?)", (NOW, NOW))
            await db.commit()

        body = (await client.request("DELETE", "/api/books/b1")).json()
        assert body["formats_deleted"] == ["ebook"], body
        assert body["requests_deleted"] == 1
        assert body["entry_deleted"] is True

        async with get_db() as db:
            assert await (await db.execute("SELECT 1 FROM books WHERE id='b1'")).fetchone() is None
            assert await (await db.execute(
                "SELECT 1 FROM requests WHERE book_id='b1'")).fetchone() is None

    @pytest.mark.asyncio
    async def test_a_request_alongside_held_formats_does_not_block_removal(self, client, library):
        """The same trap with formats present: the request type must be swept in, or
        the entry outlives the formats."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT INTO requests (id,book_id,type,status,created_at,updated_at)"
                " VALUES ('r-eb','b1','ebook','in_library',?,?)", (NOW, NOW))
            await db.commit()

        body = (await client.request("DELETE", "/api/books/b1")).json()
        assert body["entry_deleted"] is True
        async with get_db() as db:
            assert await (await db.execute("SELECT 1 FROM books WHERE id='b1'")).fetchone() is None

    @pytest.mark.asyncio
    async def test_an_explicit_subset_still_narrows(self, client, library):
        """Deriving everything must not override a caller asking for one format."""
        from app.database import get_db
        async with get_db() as db:
            await db.execute(
                "INSERT INTO requests (id,book_id,type,status,created_at,updated_at)"
                " VALUES ('r-eb','b1','ebook','in_library',?,?)", (NOW, NOW))
            await db.commit()

        body = (await client.request("DELETE", "/api/books/b1?formats=audiobook")).json()
        assert body["formats_deleted"] == ["audiobook"]
        assert body["entry_deleted"] is False
        async with get_db() as db:
            left = await (await db.execute("SELECT type FROM book_formats WHERE book_id='b1'")).fetchall()
        assert [r["type"] for r in left] == ["ebook"]
