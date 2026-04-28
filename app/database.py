import os
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = os.path.join(os.environ.get("DATA_DIR", "/data"), "athenaeum.db")

SCHEMA_VERSION = 1

SCHEMA_V1 = """
CREATE TABLE books (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    cover_url       TEXT,
    metadata_source TEXT,
    metadata_url    TEXT,
    abs_checked_at  TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE authors (
    id         TEXT PRIMARY KEY,
    name       TEXT UNIQUE NOT NULL,
    bio        TEXT,
    image_url  TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX idx_authors_name ON authors(name);

CREATE TABLE author_links (
    id                  TEXT PRIMARY KEY,
    author_id           TEXT UNIQUE REFERENCES authors(id),
    hardcover_author_id TEXT UNIQUE,
    abs_author_id       TEXT UNIQUE,
    linked_at           TEXT
);

CREATE TABLE series (
    id          TEXT PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    description TEXT,
    total_books INTEGER,
    image_url   TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX idx_series_name ON series(name);

CREATE TABLE series_links (
    id                  TEXT PRIMARY KEY,
    series_id           TEXT UNIQUE REFERENCES series(id),
    hardcover_series_id TEXT UNIQUE,
    abs_series_id       TEXT UNIQUE,
    linked_at           TEXT
);

CREATE TABLE book_authors (
    id              TEXT PRIMARY KEY,
    book_id         TEXT NOT NULL REFERENCES books(id),
    author_id       TEXT NOT NULL REFERENCES authors(id),
    author_position INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    UNIQUE(book_id, author_id)
);
CREATE INDEX idx_book_authors_book   ON book_authors(book_id);
CREATE INDEX idx_book_authors_author ON book_authors(author_id);

CREATE TABLE book_series (
    id         TEXT PRIMARY KEY,
    book_id    TEXT NOT NULL REFERENCES books(id),
    series_id  TEXT NOT NULL REFERENCES series(id),
    position   TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(book_id, series_id)
);
CREATE INDEX idx_book_series_book   ON book_series(book_id);
CREATE INDEX idx_book_series_series ON book_series(series_id);

CREATE TABLE book_links (
    id             TEXT PRIMARY KEY,
    book_id        TEXT UNIQUE REFERENCES books(id),
    abs_id         TEXT UNIQUE,
    hardcover_id   TEXT UNIQUE,
    hardcover_slug TEXT,
    linked_at      TEXT NOT NULL
);
CREATE INDEX idx_book_links_book      ON book_links(book_id);
CREATE INDEX idx_book_links_hardcover ON book_links(hardcover_id);
CREATE INDEX idx_book_links_abs       ON book_links(abs_id);

CREATE TABLE requests (
    id               TEXT PRIMARY KEY,
    book_id          TEXT NOT NULL REFERENCES books(id),
    type             TEXT NOT NULL,
    status           TEXT NOT NULL,
    narrator         TEXT,
    isbn             TEXT,
    asin             TEXT,
    abs_id           TEXT,
    abs_url          TEXT,
    last_searched_at TEXT,
    search_count     INTEGER DEFAULT 0,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
CREATE INDEX idx_requests_book   ON requests(book_id);
CREATE INDEX idx_requests_status ON requests(status);

CREATE TABLE downloads (
    id              TEXT PRIMARY KEY,
    request_id      TEXT NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    title           TEXT,
    indexer         TEXT,
    guid            TEXT UNIQUE,
    info_url        TEXT,
    protocol        TEXT,
    size            INTEGER,
    download_client TEXT,
    download_id     TEXT,
    download_path   TEXT,
    status          TEXT,
    grabbed_at      TEXT NOT NULL
);

CREATE TABLE merge_jobs (
    id             TEXT PRIMARY KEY,
    request_id     TEXT REFERENCES requests(id) ON DELETE CASCADE,
    download_id    TEXT REFERENCES downloads(id) ON DELETE CASCADE,
    source_path    TEXT NOT NULL,
    file_count     INTEGER NOT NULL,
    merged_path    TEXT,
    organized_path TEXT,
    merge_error    TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE metadata_cache (
    id           TEXT PRIMARY KEY,
    query        TEXT NOT NULL,
    source       TEXT NOT NULL,
    results_json TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    expires_at   TEXT NOT NULL
);
CREATE UNIQUE INDEX metadata_cache_query_source ON metadata_cache (query, source);
CREATE INDEX metadata_cache_expires ON metadata_cache (expires_at);

CREATE TABLE task_state (
    task        TEXT PRIMARY KEY,
    running     INTEGER NOT NULL DEFAULT 0,
    last_run    TEXT,
    last_result TEXT
);
"""


def _fold(s):
    """Lowercase + strip diacritics for accent-insensitive search."""
    import unicodedata
    if s is None:
        return None
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode("ascii")


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.create_function("fold", 1, _fold)
        yield db


async def _run_migrations(db):
    row = await (await db.execute("PRAGMA user_version")).fetchone()
    current = row[0]

    if current < 1:
        await db.executescript(SCHEMA_V1)
        await db.execute("PRAGMA user_version = 1")

    if current < 2:
        await db.execute("ALTER TABLE author_links ADD COLUMN hardcover_author_slug TEXT")
        await db.execute("ALTER TABLE series_links ADD COLUMN hardcover_series_slug TEXT")
        await db.execute("PRAGMA user_version = 2")

    if current < 3:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS book_formats (
                id                      TEXT PRIMARY KEY,
                book_id                 TEXT NOT NULL REFERENCES books(id),
                type                    TEXT NOT NULL,
                narrator                TEXT,
                abs_id                  TEXT,
                abs_url                 TEXT,
                fulfilled_by_request_id TEXT REFERENCES requests(id),
                created_at              TEXT NOT NULL,
                updated_at              TEXT NOT NULL,
                UNIQUE(book_id, type, narrator)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_book_formats_book ON book_formats(book_id)")
        # Migrate existing in_library request rows into book_formats
        await db.execute("""
            INSERT OR IGNORE INTO book_formats
                (id, book_id, type, narrator, abs_id, abs_url, fulfilled_by_request_id, created_at, updated_at)
            SELECT id, book_id, type, narrator, abs_id, abs_url, NULL, created_at, updated_at
            FROM requests WHERE status = 'in_library'
        """)
        await db.execute("DELETE FROM requests WHERE status = 'in_library'")
        await db.execute("PRAGMA user_version = 3")

    if current < 4:
        # Fix: UNIQUE(book_id, type, narrator) allows multiple NULLs in SQLite.
        # Deduplicate then normalize narrator NULL -> '' and recreate with NOT NULL.
        await db.execute("""
            DELETE FROM book_formats WHERE id NOT IN (
                SELECT MIN(id) FROM book_formats GROUP BY book_id, type, COALESCE(narrator, '')
            )
        """)
        await db.execute("UPDATE book_formats SET narrator = '' WHERE narrator IS NULL")
        await db.execute("UPDATE requests SET narrator = '' WHERE narrator IS NULL")
        await db.execute("""
            CREATE TABLE book_formats_new (
                id                      TEXT PRIMARY KEY,
                book_id                 TEXT NOT NULL REFERENCES books(id),
                type                    TEXT NOT NULL,
                narrator                TEXT NOT NULL DEFAULT '',
                abs_id                  TEXT,
                abs_url                 TEXT,
                fulfilled_by_request_id TEXT REFERENCES requests(id),
                created_at              TEXT NOT NULL,
                updated_at              TEXT NOT NULL,
                UNIQUE(book_id, type, narrator)
            )
        """)
        await db.execute("INSERT INTO book_formats_new SELECT * FROM book_formats")
        await db.execute("DROP TABLE book_formats")
        await db.execute("ALTER TABLE book_formats_new RENAME TO book_formats")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_book_formats_book ON book_formats(book_id)")
        await db.execute("PRAGMA user_version = 4")

    if current < 5:
        await db.execute("ALTER TABLE books ADD COLUMN release_date TEXT")
        await db.execute("PRAGMA user_version = 5")

    if current < 6:
        await db.execute("ALTER TABLE series ADD COLUMN show_secondary_works INTEGER DEFAULT 0")
        await db.execute("PRAGMA user_version = 6")

    if current < 7:
        await db.execute("ALTER TABLE books ADD COLUMN release_date_fetched INTEGER DEFAULT 0")
        await db.execute("PRAGMA user_version = 7")

    if current < 8:
        # ABS items have exactly one narrator — collapse UNIQUE(book_id, type, narrator)
        # to UNIQUE(book_id, type). Keep the row with a non-empty narrator per (book_id, type);
        # fall back to MIN(id) when all are empty.
        await db.execute("""
            DELETE FROM book_formats WHERE id NOT IN (
                SELECT COALESCE(
                    MIN(CASE WHEN narrator != '' THEN id END),
                    MIN(id)
                )
                FROM book_formats GROUP BY book_id, type
            )
        """)
        await db.execute("""
            CREATE TABLE book_formats_new (
                id                      TEXT PRIMARY KEY,
                book_id                 TEXT NOT NULL REFERENCES books(id),
                type                    TEXT NOT NULL,
                narrator                TEXT NOT NULL DEFAULT '',
                abs_id                  TEXT,
                abs_url                 TEXT,
                fulfilled_by_request_id TEXT REFERENCES requests(id),
                created_at              TEXT NOT NULL,
                updated_at              TEXT NOT NULL,
                UNIQUE(book_id, type)
            )
        """)
        await db.execute("INSERT INTO book_formats_new SELECT * FROM book_formats")
        await db.execute("DROP TABLE book_formats")
        await db.execute("ALTER TABLE book_formats_new RENAME TO book_formats")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_book_formats_book ON book_formats(book_id)")
        await db.execute("PRAGMA user_version = 8")

    if current < 9:
        await db.execute("""
            CREATE TABLE users (
                id                    TEXT PRIMARY KEY,
                username              TEXT NOT NULL UNIQUE,
                email                 TEXT,
                password_hash         TEXT,
                role                  TEXT NOT NULL DEFAULT 'user',
                oidc_sub              TEXT UNIQUE,
                force_password_change INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT NOT NULL,
                updated_at            TEXT NOT NULL
            )
        """)
        await db.execute("CREATE INDEX idx_users_username ON users(username)")
        await db.execute("CREATE INDEX idx_users_oidc_sub ON users(oidc_sub)")
        await db.execute("ALTER TABLE requests ADD COLUMN requested_by_user_id TEXT REFERENCES users(id)")
        await db.execute("PRAGMA user_version = 9")

    await db.commit()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await _run_migrations(db)
