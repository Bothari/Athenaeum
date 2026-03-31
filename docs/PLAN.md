# Athenaeum — Build Plan

Athenaeum is a rebuild of BookOrganizeClaude: a self-hosted book management app that
integrates AudiobookShelf (ABS), Hardcover (metadata), Prowlarr (indexers),
qBittorrent/SABnzbd (download clients), and organises completed downloads into your
media library.

This document is a complete specification. Read it entirely before writing any code.

---

## What This Is

A FastAPI + Vanilla JS SPA that lets you:

1. Browse your ABS library (synced from AudiobookShelf)
2. Search Hardcover for book metadata
3. Request missing books (audiobook or ebook)
4. Monitor and drive downloads through Prowlarr → qBittorrent/SABnzbd
5. Auto-organise completed downloads and update ABS
6. Track series completion — see what you have, what's requested, what's missing

---

## Stack

- **Backend:** Python 3.11, FastAPI, aiosqlite, httpx, PyYAML, rapidfuzz
- **Frontend:** Vanilla JS SPA (no framework, no build step), served as static files by FastAPI
- **Database:** SQLite at `/data/athenaeum.db`
- **Settings:** YAML at `/data/settings.yaml`
- **Deployment:** Docker Compose (port 8743 → 8080)

---

## File Structure

```
Athenaeum/
├── app/
│   ├── main.py                  # FastAPI app, background tasks, startup
│   ├── database.py              # Schema definition, init_db()
│   ├── settings.py              # Settings read/write helpers
│   ├── routes/
│   │   ├── books.py             # Books, authors, series, search endpoints
│   │   ├── requests.py          # Request CRUD, search-indexers, download, organize
│   │   ├── downloads.py         # Active downloads list
│   │   ├── settings.py          # Settings CRUD and connection tests
│   │   ├── metadata_links.py    # ABS↔Hardcover linking
│   │   └── enrichment.py        # Background Hardcover enrichment
│   └── services/
│       ├── audiobookshelf.py    # ABS API client
│       ├── book_search.py       # Hardcover GraphQL client
│       └── library_sync.py      # ABS → DB sync logic
├── static/
│   ├── app.js                   # Frontend SPA
│   ├── index.html               # HTML shell (contains cache buster on script tag)
│   └── style.css                # Design system
├── data/                        # Mounted volume — DB and settings live here
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── PLAN.md                      # This file
```

---

## Database Schema

### Design Principles

- **Normalised:** authors and series are separate tables with junction tables
- **No denormalised strings:** `books` has NO `author`, `series`, or `series_id` columns
- **All queries use JOINs** with `book_authors` and `book_series`
- **Explicit ID links:** `metadata_links` maps internal `book_id` → `abs_id` and/or `hardcover_id`
- **Author and series links** (`author_links`, `series_links`) map internal IDs to external IDs

### Tables

```sql
-- Core book record (no author/series columns)
CREATE TABLE books (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    cover_url    TEXT,
    metadata_source TEXT,   -- 'hardcover' | 'abs' | null
    metadata_url TEXT,
    abs_checked_at TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

-- Normalised authors
CREATE TABLE authors (
    id         TEXT PRIMARY KEY,
    name       TEXT UNIQUE NOT NULL,
    bio        TEXT,
    image_url  TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Author external IDs
CREATE TABLE author_links (
    id                  TEXT PRIMARY KEY,
    author_id           TEXT UNIQUE REFERENCES authors(id),
    hardcover_author_id TEXT UNIQUE,
    abs_author_id       TEXT UNIQUE,
    linked_at           TEXT
);

-- Normalised series
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

-- Series external IDs
CREATE TABLE series_links (
    id                TEXT PRIMARY KEY,
    series_id         TEXT UNIQUE REFERENCES series(id),
    hardcover_series_id TEXT UNIQUE,
    abs_series_id     TEXT UNIQUE,
    linked_at         TEXT
);

-- Book ↔ Author (many-to-many, ordered)
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

-- Book ↔ Series (many-to-many, with position)
CREATE TABLE book_series (
    id        TEXT PRIMARY KEY,
    book_id   TEXT NOT NULL REFERENCES books(id),
    series_id TEXT NOT NULL REFERENCES series(id),
    position  TEXT,            -- '1', '2', '4.5', 'Novella 1', etc.
    created_at TEXT NOT NULL,
    UNIQUE(book_id, series_id)
);
CREATE INDEX idx_book_series_book   ON book_series(book_id);
CREATE INDEX idx_book_series_series ON book_series(series_id);

-- ABS ↔ Hardcover ↔ internal book
CREATE TABLE metadata_links (
    id             TEXT PRIMARY KEY,
    book_id        TEXT UNIQUE REFERENCES books(id),
    abs_id         TEXT UNIQUE,       -- ABS item ID
    hardcover_id   TEXT UNIQUE,       -- Hardcover book ID
    hardcover_slug TEXT,
    linked_at      TEXT NOT NULL
);
CREATE INDEX idx_metadata_links_book      ON metadata_links(book_id);
CREATE INDEX idx_metadata_links_hardcover ON metadata_links(hardcover_id);
CREATE INDEX idx_metadata_links_abs       ON metadata_links(abs_id);

-- Download/request tracking
CREATE TABLE requests (
    id               TEXT PRIMARY KEY,
    book_id          TEXT NOT NULL REFERENCES books(id),
    type             TEXT NOT NULL,    -- 'audiobook' | 'ebook'
    status           TEXT NOT NULL,    -- see state machine below
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

-- Individual download attempts
CREATE TABLE downloads (
    id              TEXT PRIMARY KEY,
    request_id      TEXT NOT NULL REFERENCES requests(id),
    title           TEXT,
    indexer         TEXT,
    guid            TEXT,
    info_url        TEXT,
    protocol        TEXT,   -- 'torrent' | 'usenet'
    size            INTEGER,
    download_client TEXT,
    download_id     TEXT,
    download_id     TEXT,
    download_path   TEXT,
    status          TEXT,   -- 'snatched' | 'downloading' | 'completed' | 'failed'
    grabbed_at      TEXT NOT NULL
);

-- File processing after download
CREATE TABLE ingested_files (
    id                TEXT PRIMARY KEY,
    request_id        TEXT REFERENCES requests(id),
    status            TEXT,
    file_path         TEXT,
    file_type         TEXT,
    original_name     TEXT,
    is_multi_file     INTEGER,
    file_count        INTEGER,
    extracted_title   TEXT,
    extracted_author  TEXT,
    extracted_narrator TEXT,
    title             TEXT,
    author            TEXT,
    narrator          TEXT,
    metadata_source   TEXT,
    merged_file_path  TEXT,
    merge_error       TEXT,
    organized_path    TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

-- Search result cache
CREATE TABLE metadata_cache (
    id          TEXT PRIMARY KEY,
    query       TEXT,
    source      TEXT,
    results_json TEXT,
    created_at  TEXT NOT NULL
);
```

### Request State Machine

```
requested → monitored → snatched → downloading → downloaded → organizing → completed → in_library
                                                            → failed
Any state → cancelled (except in_library)
monitored → requested (can go back)
```

---

## Settings

Settings live in `/data/settings.yaml`. Read/written by `app/settings.py`.

```yaml
prowlarr:
  url: ""
  api_key: ""
  tags: []

qbittorrent:
  url: ""
  username: ""
  password: ""
  download_dir: ""

sabnzbd:
  url: ""
  api_key: ""

audiobookshelf:
  url: ""
  api_key: ""
  library_id: ""      # comma-separated if multiple

hardcover:
  api_key: ""
  preferred_language: "English"

pushover:
  app_token: ""
  user_key: ""

general:
  auto_search_interval_hours: 6
  auto_sync_interval_hours: 12
  group_series_in_search: true
  output_dir: "/output"
  separate_type_dirs: true
  audiobook_prefix: ""
  ebook_prefix: ""
```

---

## Backend

### main.py

```python
app = FastAPI()

# Include all routers under /api
app.include_router(books_router, prefix="/api")
app.include_router(requests_router, prefix="/api")
app.include_router(downloads_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(metadata_links_router, prefix="/api")
app.include_router(enrichment_router, prefix="/api")

# Serve static files
app.mount("/", StaticFiles(directory="static", html=True))

# On startup: init DB, start background tasks
@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(download_monitor())      # polls every 15s
    asyncio.create_task(library_sync_task())     # syncs on interval
    asyncio.create_task(auto_search_task())      # searches pending requests

# GET /api/status
# Returns: { books: int, requests: { requested: int, monitored: int, ... } }
```

### Background Tasks

**`download_monitor()`** — runs every 15 seconds
1. Get all requests with status in `[snatched, downloading]`
2. For each, poll the download client (qBittorrent or SABnzbd) using `download.download_id`
3. Update `downloads.status` and `requests.status` accordingly
4. On completion (status = downloaded): trigger `_auto_organize(request_id, download_path)`

**`_auto_organize(request_id, path)`** — background task
1. Read request metadata: title, author, series, series_position, type
2. Build the correct output path using settings (separate_type_dirs, prefixes)
3. Move/rename files into the output directory
4. Trigger ABS library scan
5. Poll ABS for match (title + author + type) — up to 10 retries with 5s delay
6. If found: `UPDATE requests SET status='in_library', abs_id=? WHERE id=?`
7. Also upsert into `metadata_links` (set abs_id, keep existing hardcover_id)

**`library_sync_task()`** — runs on startup (30s delay) then every N hours
1. Call `library_sync.sync_library()`
2. For each new ABS item: create book + authors + series + metadata_link

**`auto_search_task()`** — runs on configured interval
- For each `requested` request past the search interval, trigger Prowlarr search

### API Endpoints

All routes return JSON. All IDs are UUIDs (TEXT in SQLite).

#### Books (`app/routes/books.py`)

```
POST   /api/books
  Body: { title, author, cover_url?, series?, series_position?,
          metadata_source?, metadata_id?, metadata_url?,
          requests: [{type, narrator?}] }
  Returns: book detail with _created_requests, _skipped_requests counts

GET    /api/books
  Returns: [{ id, title, cover_url, authors: [...], series: [...],
              requests: [...], formats: [...] }]

GET    /api/books/{book_id}
  Returns: full book detail (same shape as list item)

DELETE /api/books/{book_id}
  Returns: { ok: true }

GET    /api/book/detail?book_id=...&abs_id=...
  Returns: enriched detail with Hardcover data and ABS matches

POST   /api/books/{book_id}/check-abs
  Queries ABS for this book and creates in_library requests if found
  Returns: { ok: true, found: bool }
```

**Book detail shape:**
```json
{
  "id": "uuid",
  "title": "...",
  "cover_url": "...",
  "metadata_source": "hardcover",
  "metadata_url": "...",
  "authors": [{"id": "uuid", "name": "...", "position": 1}],
  "series": [{"id": "uuid", "name": "...", "position": "7"}],
  "requests": [{"id": "uuid", "type": "audiobook", "status": "in_library", ...}],
  "formats": [{"type": "audiobook", "narrator": "..."}],
  "link": {"abs_id": "...", "hardcover_id": "..."}
}
```

#### Authors & Series (`app/routes/books.py`)

```
GET    /api/authors
  Returns: [{ id, name, book_count, link: {hardcover_author_id?} }]

GET    /api/authors/{author_id}/books
  Returns: [book detail shape]

GET    /api/series
  Returns: [{ id, name, book_count, link: {hardcover_series_id?} }]

GET    /api/series/{series_id}/books
  Returns: [book detail shape + position]

GET    /api/series/{series_id}/missing
  Uses get_series(hardcover_series_id) for precise list, then for each book
  fetches the most popular edition via search(title), returns missing ones
  Returns: [search result shape]

POST   /api/series/{series_id}/link
  Body: { hardcover_series_id: "..." }
  Returns: { ok: true }
```

#### Search (`app/routes/books.py`)

```
GET    /api/search/metadata?q=...
  Search Hardcover, annotate results with local data:
    - Check metadata_links for hardcover_id match → set book_id, in_library
    - Check requests for existing requests by title+author → set existing_requests
    - Fetch ABS item for in_library books → set library_formats (for dupe prevention)
  Returns: { results: [search result shape] }

GET    /api/search/advanced?title=...&author=...&series=...
  Same annotation as above
  Returns: { results: [search result shape] }
```

**Search result shape:**
```json
{
  "title": "...",
  "author": "...",
  "cover_url": "...",
  "metadata_id": "hardcover_book_id",
  "metadata_source": "hardcover",
  "series": "...",
  "series_position": "7",
  "rating": 4.2,
  "rating_count": 82,
  "users_count": 133,
  "book_id": "local_uuid_or_null",
  "in_library": false,
  "library_formats": [{"type": "audiobook"}],
  "existing_requests": [{"type": "audiobook", "status": "requested"}],
  "abs_links": []
}
```

#### Requests (`app/routes/requests.py`)

```
POST   /api/requests
  Body: { book_id, type, narrator? }
  Returns: request detail

GET    /api/requests?status=...&type=...&book_id=...
  Returns: [request detail]

GET    /api/requests/{id}
  Returns: request detail with download history

PATCH  /api/requests/{id}
  Body: { status?, narrator?, isbn?, asin? }
  Status transitions validated. Returns updated request.

DELETE /api/requests/{id}
  ACTUALLY deletes the row — does NOT set cancelled status.
  Returns: { ok: true }

POST   /api/requests/{id}/search-indexers
  Query Prowlarr for matching releases. Returns list of indexer results.

POST   /api/requests/{id}/download
  Body: { download_url, protocol, indexer?, guid?, title?, info_url?, size? }
  Sends to qBittorrent or SABnzbd depending on protocol.
  Creates download record. Updates request to 'snatched'.
  Returns: { ok: true, download_id: "..." }

POST   /api/requests/{id}/organize
  Manually trigger organize (e.g., if auto-organize failed).
  Returns: { ok: true }

POST   /api/requests/sync-library
  For all non-in_library requests, check ABS; promote if found.
  Returns: { ok: true, updated: N }
```

#### Downloads (`app/routes/downloads.py`)

```

<!-- NOTE: lines 500-749 of original were not recovered from transcript; the following section is from the reviewed/updated PLAN.md -->

#### Downloads (`app/routes/downloads.py`)

```
GET    /api/downloads
  Returns active downloads (snatched/downloading) with live progress from client.
  Each item includes: request info, download client progress, ETA, speed.
  Outbound calls to qBittorrent/SABnzbd use a 5s timeout.
  On timeout or connection error: return DB-stored status for each download with
  `client_unreachable: true` at the top level — never throw a 5xx.
  Frontend displays a warning banner when client_unreachable is true.

GET    /api/requests/{id}/downloads
  Returns all download attempts for a request
```

#### Settings (`app/routes/settings.py`)

```
GET    /api/settings
  Returns all settings grouped by category. Sensitive keys (api_key, password) returned as "********".

PUT    /api/settings
  Body: partial nested object matching the YAML structure — only included sections are updated.
  Backend deep-merges received sections into the existing YAML, then writes atomically
  (write to settings.yaml.tmp, then rename). Unknown top-level keys rejected with 400.
  Example: { "prowlarr": { "api_key": "abc" } } updates only prowlarr.api_key.
  Validates that path values (output_dir, download_dir) exist in the container. Returns { ok: true }.

POST   /api/settings/test/abs
  Tests ABS connection, returns server info and library list.

POST   /api/settings/test/prowlarr
POST   /api/settings/test/qbittorrent
POST   /api/settings/test/sabnzbd
```

#### Book Links (`app/routes/book_links.py`)

```
POST   /api/metadata-links
  Body: { book_id, abs_id?, hardcover_id? }
  Upserts the link. Returns updated link.

GET    /api/metadata-links
  Returns all links with book titles.

DELETE /api/metadata-links/{id}
  Returns { ok: true }

GET    /api/abs/search?title=...&author=...
  Searches ABS library directly. Returns ABS items.
```

#### Sync (`app/routes/sync.py`)

```
POST   /api/sync/library
  Manually trigger library_sync_task (ABS → DB upsert + HC linking).
  Returns { ok: true } immediately — sync runs in background.

POST   /api/sync/cache-refresh
  Manually trigger cache_refresh_task (refresh stale HC data).
  Returns { ok: true } immediately.

GET    /api/sync/status
  Returns status of all background sync tasks:
  { library_sync: { running, last_run, last_result },
    cache_refresh: { running, last_run, processed, total } }
```

---

## Services

### Service Instantiation Pattern

All services are **instantiated per-request** by reading current settings at call time — not module-level singletons. This means a settings change takes effect on the next request without a restart.

```python
# In a route handler:
settings = await get_settings()
abs = AudiobookshelfService(settings["audiobookshelf"])
result = await abs.get_libraries()
```

No FastAPI `Depends()` — just instantiate directly in the route handler. Services are cheap to construct (no persistent connections).

### `audiobookshelf.py`

All methods are async. Constructor takes settings dict.

```python
async def test_connection() -> dict
  # GET /api/server/info and GET /api/libraries
  # Returns: { server_version, libraries: [{id, name}] }

async def check_library(title: str, author: str) -> list[dict]
  # Fuzzy search ABS for matching items
  # Returns items with formats: [{type, narrator}]

async def search_library(query: str) -> list[dict]
  # Full text search

async def get_item_by_id(item_id: str) -> dict
  # Returns item with formats: [{type, narrator}]

async def list_all_items() -> list[dict]
  # All items across all configured library IDs
  # Each item has formats: [{type, narrator}]

async def scan_library(library_id: str = None)
  # POST /api/libraries/{id}/scan
```

**Item shape** returned by all methods:
```python
{
    "abs_id": "...",
    "abs_url": "http://...",
    "title": "...",
    "author": "...",
    "series": "...",
    "series_sequence": "7",
    "cover_url": "...",
    "narrator": "...",
    "formats": [
        {"type": "audiobook", "narrator": "...", "abs_id": "...", "abs_url": "..."},
        {"type": "ebook"}  # if also has ebook
    ]
}
```

**Important:** ABS can have a single item with BOTH audiobook and ebook formats. The `formats` array captures all. Always populate `formats` — the rest of the app depends on it.

### `book_search.py`

Hardcover GraphQL API at `https://api.hardcover.app/v1/graphql`.

```python
async def search(query: str) -> list[dict]
  # Full text search. Returns normalised results.

async def advanced_search(title=None, author=None, series=None) -> list[dict]
  # Hasura filter query.
  # If settings.group_series_in_search is true: sort results so books from the same series
  # are adjacent (sorted by series name, then position within series).
  # The JSON array stays flat — grouping is purely a sort order nicety for the frontend.

async def get_series(series_id: int) -> list[dict]
  # Fetch all books in series by Hardcover series ID.
  # Returns one result per book_series entry (may include multiple editions).
```

**GraphQL fields to request for each book:**
```graphql
id slug title subtitle description release_year pages audio_seconds
rating ratings_count users_count
cached_image cached_contributors cached_tags
contributions(order_by: {id: asc}) {
  contribution
  author { id name }
}
book_series {
  series_id position
  series { id name }
}
editions(limit: 1, where: { language: { _eq: $preferred_language } }) {
  isbn_13 asin language
  publisher { name }
  image { url }
}
```

**Normalised result shape:**
```python
{
    "title": str,
    "subtitle": str,
    "author": str,               # primary author name
    "author_id": str,            # Hardcover author ID
    "narrator": str,
    "description": str,
    "cover_url": str,
    "isbn": str,
    "asin": str,
    "pages": int,
    "publisher": str,
    "published_year": str,
    "language": str,
    "genres": list[str],
    "rating": float,
    "rating_count": int,
    "users_count": int,
    "series": list[dict],         # [{id, hardcover_series_id, name, position}], sorted: context first, then by users_count
    "is_compilation": bool,
    "compilation_details": str,
    "metadata_source": "hardcover",
    "metadata_id": str,          # Hardcover book ID
    "slug": str,
    "metadata_url": str,
    "hardcover_url": str,
}
```

**Missing books algorithm** (used in `GET /api/series/{id}/missing`):

1. Check `metadata_cache` for `(hardcover_series_id, 'hardcover_series')` with `expires_at > now`
2. **Cache hit:** use cached series data, skip to step 5
3. **Cache miss:** fetch live from HC, store in `metadata_cache` with `expires_at = now + 14 days`

> **TODO before implementing step 3:** Research the Hardcover GraphQL API to confirm whether
> a batch approach is possible — e.g. fetching multiple books by ID in one query, or
> whether `series_by_pk` can be extended to return popular-edition data directly.
> The N+1 pattern below is a known workaround for the live fetch path only.

Live fetch (cache miss only):
- Call `get_series(hardcover_series_id)` — gets precise series with positions
- For each book returned, call `search(title)` to find the most popular edition
  - 250ms delay between calls
  - On 429: retry once after `Retry-After` header value (default 10s if header absent)
  - Hard cap: if series has >50 books, process first 50 and include `truncated: true` in response
- Combine into series payload and store in cache before continuing

4. Keep `series_position` from series data, use search result for edition metadata
5. Filter out books already in our library (by hardcover_id or series position)
6. Sort results numerically by position
7. Annotate with `existing_requests` and `library_formats` (same as search endpoints)

Frontend uses AbortController so navigating away cancels any in-flight requests.

### `library_sync.py`

```python
async def sync_library() -> dict
  # Fetches all ABS items, upserts books/authors/series/links
  # Returns { synced, created, updated, errors }

async def get_sync_status() -> dict
  # Returns { running, total, processed, last_run }
```

**Sync logic per ABS item:**
1. Check `book_links` for this `abs_id`
2. **If not found (new item):**
   - Create book record (title, cover, `metadata_source='abs'`)
   - Split and create authors via `_get_or_create_author()`
   - Create series via `_get_or_create_series()`
   - Link book to authors via `book_authors`
   - Link book to series via `book_series`
   - Create `book_links` row with `abs_id`
   - Create `in_library` request for each format present
   - **Immediately attempt HC linking** via `_link_to_hardcover(book_id)` (see below)
   - Set `books.abs_checked_at = now`
   - Increment `created` counter
3. **If found (existing item):**
   - Compare title, cover_url, authors, series against stored values
   - Update any fields that have changed (`updated_at` on the book row)
   - Re-run `_get_or_create_author()` for each author (handles new authors added to item)
   - Add any new `in_library` requests for formats not already present
   - If `book_links.hardcover_id` is still NULL, retry `_link_to_hardcover(book_id)`
   - Set `books.abs_checked_at = now`
   - Increment `updated` counter only if any change was made (excluding abs_checked_at)

**`_link_to_hardcover(book_id)`** — HC linking, called inline during sync:
1. Fetch book title + author(s) from DB
2. Search HC: `search("{title} {author}")`
3. Score each result using `rapidfuzz.fuzz.token_sort_ratio` on title and author separately
4. Accept match if both title score ≥ 90 AND author score ≥ 85
5. On match:
   - Store `hardcover_id` (and `hardcover_slug` if available) in `book_links`
   - For each series linked to this book in `book_series`: fuzzy-match ABS series name to HC series names returned by search using `fuzz.token_sort_ratio` ≥ 80; store `hardcover_series_id` in `series_links`
6. On no confident match: leave `book_links.hardcover_id` NULL — user can link manually via book detail page
7. 250ms delay after each HC search call to avoid rate limiting

**`_split_authors(author_string)`:**
Lowercase the string first, then split on: `, ` | ` & ` | ` and ` | `;`
Filter out translator annotations like `(translator)`.
Restore original casing from the original string after splitting (split on lowercased copy, index back into original).
Example: `"Brandon Sanderson AND Janci Patterson"` → `["Brandon Sanderson", "Janci Patterson"]`

**`_get_or_create_author(name, abs_author_id=None, hardcover_author_id=None)`:**
1. Look up `authors` by name (case-insensitive). If not found, insert and get new `author_id`.
2. Ensure an `author_links` row exists for this author:
   ```sql
   INSERT OR IGNORE INTO author_links (id, author_id, linked_at) VALUES (?, ?, ?)
   ```
3. Set only the external ID being provided — never overwrite the other:
   ```sql
   -- When called from ABS sync:
   UPDATE author_links SET abs_author_id = ? WHERE author_id = ?
   -- When called from Hardcover enrichment:
   UPDATE author_links SET hardcover_author_id = ? WHERE author_id = ?
   ```
   This preserves existing linked IDs. `INSERT OR REPLACE` must never be used on `author_links`
   as it deletes and re-inserts the row, silently losing the other linked ID.

The same pattern applies to `_get_or_create_series()` and its `series_links` table.

### `pushover.py`

```python
async def notify_snatched(title: str, author: str, type: str, indexer: str) -> None
  # Sends a Pushover notification when a background search finds and snatches a result.
  # No-ops silently if pushover.app_token or pushover.user_key are empty.
  # POST https://api.pushover.net/1/messages.json
  # Message: "Found: {title} by {author} ({type}) — downloading from {indexer}"
  # Fire-and-forget: exceptions are logged but never raised to the caller.
```

---

## Frontend

### Design System

**This is the most important section for the rebuild. Read it carefully.**

The goal is a clean, dark, professional UI. No rounded-everything. No excessive colour.
Think a developer tool, not a consumer app.

**Colour palette:**
```css
:root {
  --bg:        #0f0f0f;
  --surface:   #1a1a1a;
  --surface2:  #252525;
  --border:    #333;
  --text:      #e0e0e0;
  --text-dim:  #888;
  --accent:    #4a9eff;
  --green:     #4caf50;
  --yellow:    #ff9800;
  --orange:    #ff5722;
  --red:       #f44336;
  --radius:    4px;
}
```

**Typography:**
- Body: system-ui, -apple-system, sans-serif
- Monospace for IDs, paths, technical values: `font-family: monospace`
- Font sizes: base 14px, headings scale from 1.1rem to 1.8rem
- `--text-dim` for secondary text, metadata, timestamps

**Spacing:**
- Base unit: 1rem = 16px
- Consistent padding on cards: 1.25rem
- Gap between grid items: 1rem
- Narrow gutters: 0.5rem

**Layout:**
**Layout:**
```
┌──────────────────────────────────────┐
│ nav (sticky top, height 48px)        │
├──────────────────────────────────────┤
│                                      │
│  main (max-width 1100px, centred)   │
│                                      │
└──────────────────────────────────────┘
```

Nav items: logo | Search | Library ▾ | Requests | Downloads | Settings

Library dropdown: Books · Authors · Series

**Cards:**
```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
}
```

No box shadows. Borders only.

**Buttons:**
```css
.btn          { padding: 0.4rem 0.9rem; border-radius: var(--radius); ... }
.btn-primary  { background: var(--accent); color: white; border: none; }
.btn-secondary{ background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
.btn-danger   { background: var(--red); color: white; border: none; }
```

**Badges** — status colours are fixed, never change:
```css
.badge { display: inline-flex; align-items: center; gap: 0.25rem;
         font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: var(--radius); }
.badge-requested    { background: #1a3a5c; color: #4a9eff; }
.badge-monitored    { background: #1a3a5c; color: #7ab8ff; }
.badge-snatched     { background: #3a2a0a; color: #ff9800; }
.badge-downloading  { background: #3a2a0a; color: #ffc107; }
.badge-downloaded   { background: #3a2a0a; color: #ffeb3b; }
.badge-organizing   { background: #2a1a0a; color: #ff5722; }
.badge-completed    { background: #1a3a2a; color: #66bb6a; }
.badge-in_library   { background: #1a3a2a; color: #4caf50; }
.badge-failed       { background: #3a1a1a; color: #f44336; }
```

### Icons

**Use a single unified icon system everywhere.** All icons are inline SVGs defined once
as JS constants at the top of `app.js`. Never use emoji or text characters as icons.

Define all icons as constants:
```javascript
const ICON_AUDIOBOOK = `<svg ...>...</svg>`;  // headphones
const ICON_EBOOK     = `<svg ...>...</svg>`;  // book
const ICON_SEARCH    = `<svg ...>...</svg>`;
const ICON_DOWNLOAD  = `<svg ...>...</svg>`;
const ICON_SETTINGS  = `<svg ...>...</svg>`;
const ICON_AUTHOR    = `<svg ...>...</svg>`;  // person
const ICON_SERIES    = `<svg ...>...</svg>`;  // stack
const ICON_LIBRARY   = `<svg ...>...</svg>`;
const ICON_REQUESTS  = `<svg ...>...</svg>`;  // list/queue
const ICON_EDIT      = `<svg ...>...</svg>`;  // pencil
const ICON_LINK      = `<svg ...>...</svg>`;  // chain link
const ICON_CHECK     = `<svg ...>...</svg>`;
const ICON_CROSS     = `<svg ...>...</svg>`;
const ICON_ARROW_UP  = `<svg ...>...</svg>`;
const ICON_ARROW_DOWN= `<svg ...>...</svg>`;
const ICON_SPINNER   = `<svg class="spin" ...>...</svg>`;  // animated
```

`typeIcon(type)` returns `ICON_AUDIOBOOK` or `ICON_EBOOK` — used EVERYWHERE a type
is displayed.

Use Lucide icon SVGs (they are clean, consistent 24px stroked icons). All icons should:
- Be 16×16 or 18×18
- Use `currentColor` for stroke/fill
- Have `stroke-width: 1.5`

### Frontend Architecture

Single file `static/app.js`. No build step. No imports. Everything is functions.

**Routing:**
```javascript
const routes = {};
function route(pattern, handler) { ... }
function navigate(path) { location.hash = '#' + path; }
function render() { /* match hash → call handler → set #app.innerHTML */ }
window.addEventListener('hashchange', render);
window.addEventListener('DOMContentLoaded', render);
```

Route params: `/library/series/:id` parsed into `{ id: "..." }`.

**API helper:**
```javascript
async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`${res.status}: ${err}`);
  }
  return res.json();
}
```

**Toasts:**
```javascript
function toast(message, type = 'success') { ... }
// type: 'success' | 'error' | 'info'
// Auto-dismiss after 3 seconds
```

**Shared render functions — define once, use everywhere:**

```javascript
// Renders a table with sortable columns and text filter
// config: { headers: [{label, key, style}], rows: [...html strings] }
function renderTable(config) { ... }

// Renders a book card (for grid view)
function renderBookCard(book) { ... }

// Renders an author card
function renderAuthorCard(author) { ... }

// Renders a series card
function renderSeriesCard(series) { ... }

// Renders search result cards (Hardcover results with request form)
// onRequestSuccess: optional callback, if not provided navigates to book detail
function renderSearchResults(container, results, onRequestSuccess = null) { ... }

// Returns inline confirmation handler (click once → warning state → click again → action)
// Used for delete buttons everywhere
function confirmAction(btn, confirmText, action) { ... }

// Renders a stats header card for author/series detail pages
function renderDetailStats(name, stats) { ... }
// stats: { inLibrary: N, total: N, requested: N, missing: N, loadingMissing: bool }
```

**`expandRequestForm(slot, result, onSuccess = null)`:**
- Shows format selection (audiobook/ebook), disabled if already have it
- Checks `result.existing_requests` AND `result.library_formats` for each format
- On submit: POST /api/books (creates book + requests), then POST /api/requests if book already existed
- On success: call `onSuccess(createdBook, result, selectedTypes)` or navigate to book detail

### Frontend Routes

```
/#/                          Dashboard
/#/search                    Search page (quick + advanced)
/#/library/books             Books list (table/grid, filterable)
/#/library/authors           Authors list (table/grid)
/#/library/authors/:id       Author detail
/#/library/series            Series list (table/grid)
/#/library/series/:id        Series detail
/#/library/book?book_id=...  Book detail
/#/requests/:id              Request detail
/#/downloads                 Active downloads
/#/settings                  Settings
```

### Key Page Behaviours

**Search page (`/#/search`):**
- Quick search: single query field, search Hardcover
- Advanced search: title + author + series fields
- Results rendered with `renderSearchResults(container, results, onSearchRequestSuccess(container))`
- `onSearchRequestSuccess`: stays on page, updates card in-place (no navigation)
- Card updates: shows new request badge, disables format button with "(have)" label

**Series detail (`/#/library/series/:id`):**
- Loads books from DB immediately (fast)
- Loads missing books async in background
- Stats card shows loading state (`⟳ loading...`) while missing books load
- Stats card updates when missing done: `N/Total in library | X requested | Y missing | Z%`
- Requesting from missing books: updates in-place, moves from missing to library table
- All stats update live as requests are added

**Book detail (`/#/library/book?book_id=...`):**
- Shows book metadata (from DB + Hardcover if linked)
- Shows ABS items: the linked item + potential matches
- Shows all requests with expandable dropdown
- Request dropdown has: Search Prowlarr button + Delete Request button
- Delete: click once → "Click again to confirm" (orange) → click again → deleted, removed from DOM

**Request detail (`/#/requests/:id`):**
- Full request info, status history
- Prowlarr search results with one-click download
- Download history

**Downloads (`/#/downloads`):**
- Polls every 5 seconds
- Shows speed, ETA, progress bar for each active download

---

## Important Implementation Notes

### SQL Query Patterns

Never SELECT columns that don't exist. Always use JOINs for authors and series.

**Get book with authors and series:**
```sql
SELECT b.id, b.title, b.cover_url,
       GROUP_CONCAT(DISTINCT a.name) as authors,
       GROUP_CONCAT(DISTINCT s.name) as series_names
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_series bs ON b.id = bs.book_id
LEFT JOIN series s ON bs.series_id = s.id
WHERE b.id = ?
GROUP BY b.id
```

**Important:** SQLite's GROUP_CONCAT does NOT support DISTINCT with a custom separator.
Use `GROUP_CONCAT(a.name, ', ')` or `GROUP_CONCAT(DISTINCT a.name)` (comma only). 
If you need ordered authors, subquery or sort in Python after fetching.

### Preventing Duplicate Requests

`library_formats` is fetched by calling `audiobookshelf.get_item_by_id(abs_id)` for 
each in-library book when annotating search results. This tells the frontend which
formats are physically present in ABS, so request form buttons can be disabled.

Do NOT use request status to infer library presence — requests can be stale.

### Request Deletion

**Always DELETE the row.** Never set status to 'cancelled'. Cancelled status was a
historical mistake that caused bugs (duplicate prevention thought requests existed
when they'd been "deleted"). The DELETE endpoint removes the row entirely.

### Series Missing Books

The correct algorithm is:
1. `get_series(hardcover_series_id)` — precise list with positions
2. For EACH book returned, do a fresh `search(title)` to get the most popular edition
   (Hardcover's series endpoint returns unpopular editions; search returns popular ones)
3. Keep `series_position` from step 1, replace everything else from step 2's best match
4. `best match` = exact title match with highest `users_count`, then `rating_count`
5. Filter: skip if `hardcover_id` is in our `metadata_links`, OR if `series_position` matches a book we already have
6. Sort numerically: `float(position)` for numeric positions, put non-numeric last
7. Annotate with `library_formats` and `existing_requests`

### ABS Format Detection

ABS items can have both audiobook and ebook formats. Detect via:
```python
def _extract_formats(media, metadata):
    formats = []
    # audiobook: media.tracks exists and has entries
    if media.get('tracks') or media.get('audioFiles'):
        formats.append({'type': 'audiobook', 'narrator': metadata.get('narratorName', '')})
    # ebook: media.ebookFile exists
    if media.get('ebookFile'):
        formats.append({'type': 'ebook'})
    return formats
```

---

## Building Order

Build in this order. Each phase should be working before starting the next.

### Phase 1: Foundation
1. `Dockerfile` and `requirements.txt`
2. `app/database.py` — full schema, `init_db()` function
3. `app/settings.py` — read/write settings YAML
4. `app/main.py` — bare FastAPI app, static file serving, DB init on startup
5. `static/index.html` — HTML shell with nav, `<div id="app">`, script tag
6. `static/style.css` — full design system (variables, cards, badges, buttons, layout, tables, grid)
7. `static/app.js` — router, api(), toast(), all icon constants, shared render functions skeleton

### Phase 2: Settings & ABS
8. `app/services/audiobookshelf.py` — all methods
9. `app/routes/settings.py` — GET/PUT settings, 4 connection test endpoints
10. Settings page in frontend — form groups, test buttons, save

### Phase 3: Library Sync
11. `app/services/library_sync.py` — sync_library(), helpers
12. `app/routes/books.py` (partial) — GET /api/books, GET /api/authors, GET /api/series
13. Library pages: Books list, Authors list, Series list (table + grid views)

### Phase 4: Search & Requests
14. `app/services/book_search.py` — all search methods
15. `app/routes/books.py` (complete) — search endpoints, series missing, book detail
16. Search page frontend — quick + advanced, in-place request success
17. `app/routes/requests.py` — CRUD, sync-library
18. Request-related UI on book cards and detail pages

### Phase 5: Downloads
19. `app/routes/requests.py` — search-indexers, download, organize endpoints
20. `app/routes/downloads.py`
21. `app/main.py` — download_monitor background task
22. Request detail page, Downloads page

### Phase 6: Detail Pages
23. Book detail page — metadata, ABS linking, request management
24. Author detail page — books, stats
25. Series detail page — books, completion, missing books (async loading)
26. `app/routes/metadata_links.py`
27. `app/routes/enrichment.py`

### Phase 7: Polish
28. Dashboard stats
29. Active download polling
30. Library sync progress
31. Enrichment progress
32. Mobile/responsive CSS fixes

---

## What Went Wrong in BookOrganizeClaude (Learn From This)

- **Code rot from iteration:** Logic was spread between routes, main.py, and services with duplication.
  Keep each concern in ONE place.

- **Schema denormalisation:** Early versions had author/series as strings in books table.
  We normalised later, which required rewriting dozens of queries. Start normalised.

- **Inconsistent icons:** Some pages used emoji, some used SVG, some used text.
  Define ALL icons as constants at the top of app.js and use them everywhere.

- **Search vs series endpoint returning different editions:** Hardcover's `series_by_pk`
  returns unpopular editions while `books` search returns popular ones. The workaround
  (search by title for each book) is correct — don't try to simplify it.

- **request status='cancelled' for deletes:** Caused duplicate prevention to falsely
  block new requests. Always hard-delete.

- **Navigation on request submit:** Submitting a request from search/series pages
  navigated away, making it impossible to request multiple books quickly.
  Always provide `onSuccess` callbacks instead of navigating.

- **library_formats reliability:** Checking `requests.status = 'in_library'` to infer
  formats was unreliable (requests don't always get updated). Fetch from ABS directly.

- **GROUP_CONCAT with DISTINCT and custom separator:** SQLite doesn't support this.
  Use subqueries or post-process in Python.

- **Cache busters:** Must bump the `?v=N` on the script tag in index.html every time
  app.js changes. Forget this → users see old JS.

---

## Settings File Location

The existing settings file from BookOrganizeClaude has been copied to:
`/home/max/Projects/Athenaeum/data/settings.yaml`

It contains real API keys and service URLs. The new app should read from the same path.

---

## Deployment

```bash
# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f

# Rebuild after any change
docker compose up -d --build
```

Port: **8743** (different from BookOrganizeClaude's 8742, so both can run simultaneously)


