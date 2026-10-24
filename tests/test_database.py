import aiosqlite
import pytest


EXPECTED_TABLES = {
    "books",
    "authors",
    "author_links",
    "series",
    "series_links",
    "book_authors",
    "book_series",
    "book_links",
    "requests",
    "downloads",
    "merge_jobs",
    "metadata_cache",
    "task_state",
    "book_formats",
    "users",
}


async def test_migrations_set_user_version(db_path):
    async with aiosqlite.connect(db_path) as db:
        row = await (await db.execute("PRAGMA user_version")).fetchone()
        assert row[0] == 17


async def test_all_tables_created(db_path):
    async with aiosqlite.connect(db_path) as db:
        rows = await (
            await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
        tables = {row[0] for row in rows}
        assert EXPECTED_TABLES <= tables


async def test_migrations_disable_fk_enforcement_on_any_connection(tmp_path):
    """Table-rebuild migrations (CREATE new -> copy -> DROP old -> RENAME) fail
    under foreign_keys=ON when other tables reference the rebuilt one — but only
    on populated databases, so a suite that migrates empty DBs never catches it.
    _run_migrations must pin FK enforcement OFF itself rather than inherit
    whatever the caller's connection has set."""
    from app.database import _run_migrations
    path = str(tmp_path / "fk-on.db")
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        await _run_migrations(db)
        row = await (await db.execute("PRAGMA foreign_keys")).fetchone()
        assert row[0] == 0  # the runner pinned it OFF for its own connection
        tables = {r[0] for r in await (await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")).fetchall()}
        assert "users" in tables  # migrations actually ran to completion


async def test_migrations_are_idempotent(tmp_path, monkeypatch):
    """Running init_db() twice on the same DB must not raise or corrupt schema."""
    path = str(tmp_path / "idempotent.db")
    monkeypatch.setattr("app.database.DB_PATH", path)
    from app.database import init_db
    await init_db()
    await init_db()
    async with aiosqlite.connect(path) as db:
        row = await (await db.execute("PRAGMA user_version")).fetchone()
        assert row[0] == 17


@pytest.mark.asyncio
async def test_migration_16_keeps_the_two_meanings_of_completed_apart(tmp_path, monkeypatch):
    """`downloads` and `series_downloads` both used 'completed', for different states.

    In `downloads` it meant the download had finished. In `series_downloads` it
    meant the pack was fully organised, and a finished download there was
    'downloaded'. Mapping downloaded -> completed alone collapses the terminal
    state into a mid-pipeline one, and the startup sweep then re-organises packs
    that were already finished.
    """
    import aiosqlite
    from app import database as db_mod

    db_file = str(tmp_path / "v15.db")
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)

    async with aiosqlite.connect(db_file) as db:
        await db.execute("""CREATE TABLE downloads (
            id TEXT PRIMARY KEY, request_id TEXT, title TEXT, indexer TEXT,
            guid TEXT UNIQUE, info_url TEXT, protocol TEXT, size INTEGER,
            download_client TEXT, download_id TEXT, download_path TEXT,
            status TEXT, grabbed_at TEXT NOT NULL)""")
        await db.execute("""CREATE TABLE series_downloads (
            id TEXT PRIMARY KEY, series_id TEXT NOT NULL, type TEXT NOT NULL DEFAULT 'ebook',
            title TEXT, indexer TEXT, guid TEXT UNIQUE, info_url TEXT, protocol TEXT,
            size INTEGER, download_client TEXT, download_id TEXT, download_path TEXT,
            status TEXT NOT NULL DEFAULT 'snatched', grabbed_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, proposed_mappings TEXT)""")
        # one pack in each state that matters
        for pid, status in [("p-done", "completed"), ("p-dl", "downloaded"),
                            ("p-org", "organizing"), ("p-fail", "failed")]:
            await db.execute(
                "INSERT INTO series_downloads (id, series_id, guid, status, grabbed_at, updated_at)"
                " VALUES (?,?,?,?,'t','t')", (pid, "s1", "guid-" + pid, status))
        await db.execute(
            "INSERT INTO downloads (id, request_id, guid, status, grabbed_at)"
            " VALUES ('d1','r1','guid-d1','completed','t')")
        # A real v15 database has these from SCHEMA_V1. The fixture only builds
        # what migration 16 touches, so later migrations that reach other tables
        # need them present too — migration 17 rewrites book_series positions.
        await db.execute("""CREATE TABLE book_series (
            id TEXT PRIMARY KEY, book_id TEXT NOT NULL, series_id TEXT NOT NULL,
            position TEXT, created_at TEXT NOT NULL, UNIQUE(book_id, series_id))""")
        await db.execute(
            "INSERT INTO book_series (id, book_id, series_id, position, created_at)"
            " VALUES ('bs-whole','b1','s1','1.0','t'), ('bs-frac','b2','s1','3.5','t'),"
            "        ('bs-text','b3','s1','1-2','t')")
        await db.execute("PRAGMA user_version = 15")
        await db.commit()

    await db_mod.init_db()

    async with aiosqlite.connect(db_file) as db:
        cur = await db.execute("PRAGMA user_version")
        assert (await cur.fetchone())[0] == 17

        cur = await db.execute("SELECT id, status, kind FROM downloads ORDER BY id")
        rows = {r[0]: (r[1], r[2]) for r in await cur.fetchall()}

        # the finished download keeps its meaning in both vocabularies
        assert rows["d1"] == ("completed", "request")
        assert rows["p-dl"] == ("completed", "series_pack")
        # the pack terminal state is renamed so it cannot be confused with it
        assert rows["p-done"] == ("organized", "series_pack")
        # everything else is carried across untouched
        assert rows["p-org"] == ("organizing", "series_pack")
        assert rows["p-fail"] == ("failed", "series_pack")

        # the regression itself: the startup sweep must not pick up finished packs
        cur = await db.execute(
            "SELECT count(*) FROM downloads WHERE kind='series_pack'"
            " AND status IN ('completed','organizing')")
        assert (await cur.fetchone())[0] == 2, "only the mid-pipeline packs"

        cur = await db.execute("SELECT name FROM sqlite_master WHERE name='series_downloads'")
        assert await cur.fetchone() is None

        # migration 17: whole numbers lose the decimal, fractions and text survive
        cur = await db.execute("SELECT id, position FROM book_series ORDER BY id")
        positions = {r[0]: r[1] for r in await cur.fetchall()}
        assert positions == {"bs-frac": "3.5", "bs-text": "1-2", "bs-whole": "1"}, positions
