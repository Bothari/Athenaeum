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
