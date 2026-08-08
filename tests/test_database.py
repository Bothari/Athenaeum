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
    "series_downloads",
}


async def test_migrations_set_user_version(db_path):
    async with aiosqlite.connect(db_path) as db:
        row = await (await db.execute("PRAGMA user_version")).fetchone()
        assert row[0] == 14


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
        assert row[0] == 14
