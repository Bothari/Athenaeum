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
│   │   ├── book_links.py        # ABS↔Hardcover linking
│   │   └── sync.py              # Manual sync triggers + status
│   └── services/
│       ├── audiobookshelf.py    # ABS API client
│       ├── book_search.py       # Hardcover GraphQL client
│       ├── library_sync.py      # ABS → DB sync logic
│       └── pushover.py          # Pushover notification client
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

### Database Connection

Never call `aiosqlite.connect()` directly. Always use the `get_db()` helper, which sets required PRAGMAs on every connection:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")   # concurrent readers + one writer
        await db.execute("PRAGMA busy_timeout=5000")  # retry up to 5s before raising
        await db.execute("PRAGMA foreign_keys=ON")    # enforce FK constraints
        yield db

# Usage everywhere:
async with get_db() as db:
    ...
```

WAL mode allows concurrent reads alongside writes instead of exclusive locking. `busy_timeout` retries on contention before raising `OperationalError: database is locked`. `foreign_keys=ON` must be set per-connection in SQLite — it does not persist.

### Migration Strategy

`database.py` uses a `PRAGMA user_version`-based migration system. **Never use bare `CREATE TABLE IF NOT EXISTS`** — all schema lives inside versioned migration blocks.

```python
SCHEMA_VERSION = 1  # bump when adding migrations

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await _run_migrations(db)

async def _run_migrations(db):
    row = await (await db.execute("PRAGMA user_version")).fetchone()
    current = row[0]

    if current < 1:
        await db.executescript(SCHEMA_V1)  # all CREATE TABLE statements
        await db.execute("PRAGMA user_version = 1")

    # Future migrations go here:
    # if current < 2:
    #     await db.executescript("ALTER TABLE books ADD COLUMN foo TEXT")
    #     await db.execute("PRAGMA user_version = 2")

    await db.commit()
```

`SCHEMA_V1` is a string constant containing all `CREATE TABLE` and `CREATE INDEX` statements. Future schema changes are additive `ALTER TABLE` blocks in numbered `if current < N` guards. Never edit past migration blocks.

### Design Principles

- **Normalised:** authors and series are separate tables with junction tables
- **No denormalised strings:** `books` has NO `author`, `series`, or `series_id` columns
- **All queries use JOINs** with `book_authors` and `book_series`
- **Explicit ID links:** `book_links` maps internal `book_id` → `abs_id` and/or `hardcover_id`
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
    abs_checked_at TEXT,  -- set by library_sync on every run; NULL means never synced
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
CREATE INDEX idx_authors_name ON authors(name);

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

-- ABS ↔ Hardcover ↔ internal book (mirrors author_links / series_links pattern)
CREATE TABLE book_links (
    id             TEXT PRIMARY KEY,
    book_id        TEXT UNIQUE REFERENCES books(id),
    abs_id         TEXT UNIQUE,       -- ABS item ID (one per book — see separate_type_dirs note)
    hardcover_id   TEXT UNIQUE,       -- Hardcover book ID
    hardcover_slug TEXT,
    linked_at      TEXT NOT NULL
);
CREATE INDEX idx_book_links_book      ON book_links(book_id);
CREATE INDEX idx_book_links_hardcover ON book_links(hardcover_id);
CREATE INDEX idx_book_links_abs       ON book_links(abs_id);

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
    request_id      TEXT NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
    title           TEXT,
    indexer         TEXT,
    guid            TEXT UNIQUE,
    info_url        TEXT,
    protocol        TEXT,   -- 'torrent' | 'usenet'
    size            INTEGER,
    download_client TEXT,
    download_id     TEXT,
    download_path   TEXT,
    status          TEXT,   -- 'snatched' | 'downloading' | 'completed' | 'failed'
    grabbed_at      TEXT NOT NULL
);

-- Merge job tracking (only created when multi-file merge is performed)
-- Lifecycle is tracked via requests.status — this table stores file-system details only
CREATE TABLE merge_jobs (
    id             TEXT PRIMARY KEY,
    request_id     TEXT REFERENCES requests(id) ON DELETE CASCADE,
    download_id    TEXT REFERENCES downloads(id) ON DELETE CASCADE,
    source_path    TEXT NOT NULL,  -- original download folder
    file_count     INTEGER NOT NULL,
    merged_path    TEXT,           -- path to output .m4b (set on success)
    organized_path TEXT,           -- final destination path (set after move)
    merge_error    TEXT,           -- ffmpeg stderr on failure
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

-- HC data cache: books, series, authors
-- query = hardcover ID, source = 'hardcover_book' | 'hardcover_series' | 'hardcover_author'
-- TTL: 14 days (expires_at = created_at + 14 days)
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

-- Scheduled task state (persists across restarts)
-- One row per scheduled task; upserted at start and end of each run.
CREATE TABLE task_state (
    task        TEXT PRIMARY KEY,  -- 'library_sync' | 'cache_refresh' | 'auto_search'
    running     INTEGER NOT NULL DEFAULT 0,  -- 1 while task is executing
    last_run    TEXT,              -- ISO timestamp of last completed run
    last_result TEXT               -- 'ok' | 'error: <message>'
);
```

### Request State Machine

```
requested → snatched → downloading → downloaded → merging (optional) → organizing → in_library
                                                                   ↘ (no merge)  ↑
                                                                     organizing → failed
```

`monitored` is not a status. All `requested` items are eligible for auto-search if `schedule.auto_search` is configured and non-empty. To stop auto-searching, clear (disable) the auto_search schedule — not by changing individual request statuses.

`merging` — ffmpeg m4b merge in progress (only for multi-file audiobooks when `merge_multifile_audiobooks` is enabled)
`organizing` — file move in progress, ABS scan triggered, polling for match

Valid terminal states: `in_library`, `failed`.
`failed` can be retried: `POST /api/requests/{id}/organize` re-runs `_auto_organize`, transitioning back through `merging` or `organizing` as appropriate.
There is no `cancelled` state — always hard-delete the row (see Request Deletion below).

---

## Settings

Settings live in `/data/settings.yaml`. Read/written by `app/settings.py`.

`app/settings.py` exposes two async functions — `get_settings()` and `save_settings(partial)` — and a module-level `asyncio.Lock` that both acquire before touching the file. This serialises concurrent reads (background tasks at startup) and writes (user saving a settings tab).

```python
_settings_lock = asyncio.Lock()

async def get_settings() -> dict:
    async with _settings_lock:
        # load and return yaml

async def save_settings(partial: dict) -> None:
    async with _settings_lock:
        # load current, deep-merge partial, write to settings.yaml.tmp, rename to settings.yaml
```

No other module reads or writes the YAML directly — all access goes through these two functions.

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
  library_id: []      # list of library IDs (single or multiple)

hardcover:
  api_key: ""
  preferred_language: "English"

pushover:
  app_token: ""
  user_key: ""

general:
  group_series_in_search: true
  output_dir: "/output"
  separate_type_dirs: true
  audiobook_prefix: ""
  ebook_prefix: ""
  merge_multifile_audiobooks: false

schedule:
  library_sync:    "0 2 * * *"   # ABS → DB upsert + inline HC linking
  cache_refresh:   "0 3 * * *"   # refresh stale HC data (books, series, authors) — 1hr time slice
  auto_search:     "0 */6 * * *" # search Prowlarr for pending requests

auth:
  mode: "none"              # "none" | "form" | "oidc"

  # Form login (single user)
  username: "admin"
  password_hash: ""         # bcrypt hash — set via Settings UI, never store plaintext

  # OIDC
  oidc_provider_url: ""     # e.g. https://accounts.google.com
  oidc_client_id: ""
  oidc_client_secret: ""
  oidc_scopes: "openid email profile"

  # Session (shared by both form and OIDC)
  session_secret: ""        # 32-byte random hex — auto-generated on first startup if empty
  session_days: 7
```

---

## Implementation Notes

Non-obvious details and gotchas from BookOrganizeClaude (the predecessor). Referenced when building Phases 5 and 6.

### Hardcover: Series Missing Books

`series_by_pk` returns one entry per series position, but the book it returns is often an obscure or foreign-language edition with low `users_count`. Do **not** use its metadata directly for the missing-books feature.

**Correct approach:**
1. Fetch the series to get the canonical list of positions and titles.
2. For each position, call `search(title)` and pick the most popular matching result.
3. Keep `series_position` from the series endpoint; all other metadata (cover, description, ISBN) comes from the search result.

**Best-edition selection** (applied to candidates from `search(title)`):
1. Sort by `users_count DESC, ratings_count DESC, rating DESC`
2. Language filter: prefer editions whose `language` matches `preferred_language` setting; pass through entries with no language set; drop entries with a known non-preferred language
3. Take the first result

### Hardcover: Compilation Detection

A book is a compilation if any of:
- `book_series.compilation` is truthy
- `position` or `details` string contains a comma or ampersand
- `position` or `details` matches `\d+\s*-\s*\d+` (a range like "1-3")

Compilations sort after their last included book: `"1-3"` sorts after position `3`. Use `float(series_position)` for numeric sort; handle `ValueError` (non-numeric positions) by placing them last.

### ABS: Fuzzy Author Matching

When checking if a download matches a book in ABS, search by title only — combined title+author ABS search is unreliable. Filter results by fuzzy author:

```python
def _fuzzy_match(query, target):
    q = query.lower().replace(".", "").replace(" ", "")
    t = target.lower().replace(".", "").replace(" ", "")
    return q in t or t in q
```

Handles `"S. A. Corey"` vs `"S.A. Corey"` and similar period/spacing variants.

### ABS: Series Name Parsing

ABS stores series in `metadata.seriesName` as a string like `"Honor Harrington #9"` or `"Series A #1, Series B #2"`. Newer ABS versions may provide `metadata.series` as an array of `{name, sequence}` objects — check that first, fall back to parsing the string.

Parsing the string:
1. Split on comma for multiple series
2. For each part, regex-match position patterns: `#N`, `Book N`, `Vol N` (where N is `\d+(?:\.\d+)?`)
3. Strip the position marker from the series name

### qBittorrent: Auth

Cookie-based session auth. Login: `POST /api/v2/auth/login` with form data `{username, password}`. On success the response sets a `SID` cookie — cache and reuse it globally. On any `403`, re-authenticate and retry the original request once.

### qBittorrent: Hash Resolution

qBittorrent does not return the torrent hash from the add call. Two strategies:

- **Magnet link:** parse `btih:([a-fA-F0-9]{40})` from the URI directly.
- **.torrent file URL:** download the file, extract the bencoded `info` dict, SHA1-hash it (requires a minimal bencode parser — just enough to extract the `info` key).

After adding, poll `GET /api/v2/torrents/info?hashes={hash}` every 500ms up to 20 times (10s total). Raise an error if the torrent hasn't appeared after 20 polls.

### qBittorrent: State Mapping

| qBit states | Normalised |
|---|---|
| `uploading`, `stalledUP`, `forcedUP`, `pausedUP`, `queuedUP` | `completed` |
| `downloading`, `stalledDL`, `forcedDL`, `metaDL` | `downloading` |
| `pausedDL`, `queuedDL` | `paused` |
| `error`, `missingFiles` | `failed` |

For the completed download path, use `content_path` (the direct path to the file or folder). Fall back to `save_path + "/" + name` if `content_path` is absent.

### Download Clients: Copy vs Move

For qBittorrent (torrents): **copy** files to the output directory. Leave originals intact for seeding.
For SABnzbd (usenet): **move** files — no seeding, safe to move.

```python
use_copy = (download_client == "qbittorrent")
```

### Prowlarr: API Details

Auth header is `X-Api-Key: <key>` — not `Authorization: Bearer`.

Search: `GET /api/v1/search?query={q}&type=search&limit=50`

Each result: `{ protocol, downloadUrl, guid, title, indexer, size, infoUrl }`.
Route by `protocol`: `"torrent"` → qBittorrent, `"usenet"` → SABnzbd.

### M4B Merge: Codec Selection and File Order

When all input files are `.m4a` or `.m4b`, use `-c copy` (stream copy, no re-encode — fast, no quality loss). Only fall back to `-c:a aac -b:a {avg_bitrate}k` for mixed-format inputs.

Input files must be sorted by **natural/numeric order** before merging — plain alphabetical sort breaks on `Part01, Part2, Part10`.

### metadata.json (ABS-compatible)

Write to the organised target directory alongside the audio/ebook files. ABS reads this on library scan.

```json
{
  "title": "...",
  "subtitle": "...",
  "authors": ["Author One", "Author Two"],
  "narrators": ["Narrator Name"],
  "series": ["Series Name #3"],
  "genres": ["Science Fiction"],
  "publishedYear": "2003",
  "publisher": "Baen Books",
  "description": "...",
  "isbn": "9781234567890",
  "asin": "B00XXXXX",
  "language": "English"
}
```

Rules:
- `authors` and `narrators` are arrays
- `series` entries are `"Name #Position"` strings — omit `#position` if unknown
- `publishedYear` is a string, not integer
- Omit keys entirely when the value is empty or null

### Post-Organize: ABS Scan Polling

After moving files to the output directory:
1. Trigger `POST /api/libraries/{lib_id}/scan`
2. Wait 5 seconds (ABS scan is asynchronous)
3. Poll `check_library(title, author, type)` — up to 10 retries with 5s between each
4. On match: update `book_links` with `abs_id`; set request to `completed` (it becomes a `book_formats` entry on the next library sync)
5. On retries exhausted: set `requests.status = 'failed'`, log reason — the next library sync will pick it up

### SQLite: GROUP_CONCAT with DISTINCT

`GROUP_CONCAT(DISTINCT col, ', ')` is **not valid** in SQLite — the DISTINCT aggregate form accepts only one argument. Use `GROUP_CONCAT(col, ', ')` without DISTINCT, or deduplicate via a subquery first.

### UI: Two-Click Destructive Actions

Inline two-click confirmation for irreversible actions (delete request, unlink, etc.):
1. First click: change button to warning colour with label "Confirm?"
2. Second click: execute

Do **not** use `window.confirm()` (blocks the thread, looks bad on mobile). Do **not** use `:contains()` CSS selectors (jQuery syntax, not valid in plain CSS).

---

## Authentication

> WARNING: THIS SECTION NEEDS REVIEW BEFORE IMPLEMENTATION
>
> The auth design below is a first draft and has not been adversarially reviewed.
> Before building Phase 8, treat this section the same as the original PLAN.md
> went through review — check for security gaps, missing edge cases, and
> implementation complexity. In particular: session management, OIDC flow
> correctness, API auth (see below), and whether the single-user form model
> is sufficient. Do not implement from this spec as-is.

### Overview

Three modes, selected in Settings → Auth. Default is `none` — no change to current behaviour. The mode takes effect immediately on save; no restart needed.

- **none** — all routes are open. Suitable for a trusted local network.
- **form** — single-user username + bcrypt password. Login form in the SPA.
- **oidc** — OAuth2 Authorization Code + PKCE flow against any standards-compliant provider (Google, Authentik, Keycloak, etc.). No user management — if OIDC auth succeeds, access is granted.

### Session Strategy

Both `form` and `oidc` use a **signed JWT in an httponly cookie** (`session`):

- Signed with `auth.session_secret` using HS256
- Payload: `{ sub: "<username or oidc_subject>", iat, exp }`
- Expiry: `auth.session_days` days from issue
- Cookie flags: `httponly=True`, `samesite="lax"`, `secure` only when the request came over HTTPS (detected via `X-Forwarded-Proto` header)

`session_secret` is auto-generated (32-byte hex via `secrets.token_hex(32)`) and persisted to settings.yaml on first startup if empty. Changing it invalidates all existing sessions.

### Dependencies

Add to `requirements.txt`:
```
python-jose[cryptography]   # JWT sign/verify
passlib[bcrypt]             # password hashing (form mode)
```

### FastAPI auth dependency

`app/auth.py` — single file for all auth logic.

```python
async def require_auth(request: Request) -> str:
    """Returns subject (username or OIDC sub) or raises 401."""
    settings = await get_settings()
    if settings["auth"]["mode"] == "none":
        return "anonymous"
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, settings["auth"]["session_secret"], algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(401, "Invalid session")
```

Applied via `Depends(require_auth)` on every router. Routes that must be **exempt** from auth:
- `GET /healthz`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/oidc/start`
- `GET /api/auth/oidc/callback`

Static files (`/static/*`) are never gated — they are just JS/CSS with no sensitive data.

### Auth routes (`app/routes/auth.py`)

```
POST /api/auth/login
  Body: { username, password }
  Form mode only. Verifies password against bcrypt hash.
  On success: set session cookie, return { ok: true, username }.
  On failure: 401 { error: "Invalid credentials" } — same message for wrong user or wrong password.

POST /api/auth/logout
  Clears the session cookie. Returns { ok: true }.

GET  /api/auth/me
  Returns { username } if session valid, 401 otherwise.
  Called by frontend on boot to determine auth state.

GET  /api/auth/oidc/start
  OIDC mode only.
  Generates state (random 16 bytes hex), nonce, code_verifier, code_challenge (S256).
  Stores { state, nonce, code_verifier } in a short-lived (10 min) httponly cookie `oidc_state`.
  Redirects to provider's authorization_endpoint.

GET  /api/auth/oidc/callback?code=...&state=...
  OIDC mode only.
  1. Verify state matches oidc_state cookie — 400 if mismatch.
  2. POST to token_endpoint: exchange code + code_verifier for tokens.
  3. Verify ID token signature and nonce claim.
  4. Extract sub (and email if present) as the session subject.
  5. Set session cookie, clear oidc_state cookie.
  6. Redirect to /.
```

### OIDC flow detail

Athenaeum implements the PKCE flow manually using `httpx` — no heavy OIDC library required.

**Discovery:** On first OIDC request, fetch `{oidc_provider_url}/.well-known/openid-configuration` to get `authorization_endpoint`, `token_endpoint`, `jwks_uri`. Cache in memory for the process lifetime (re-fetched on restart).

**PKCE:** `code_verifier` = 32-byte random URL-safe base64. `code_challenge` = base64url(sha256(code_verifier)). Method: `S256`.

**ID token verification:** Fetch JWKS from `jwks_uri`. Verify signature, `iss`, `aud` (must equal `client_id`), `exp`, `nonce`. Use `python-jose` for this.

**Redirect URI:** Always `{request.base_url}api/auth/oidc/callback`. This must be registered with the OIDC provider.

### Password management (form mode)

Setting a password via the Settings UI:
```
PUT /api/settings  { "auth": { "password_hash": "<bcrypt hash>" } }
```

The Settings UI never sends the raw password to the server — it hashes with bcrypt **client-side** before sending... actually no: hashing on the server is correct. The UI sends the raw password to `POST /api/auth/set-password` which hashes it server-side before storing.

```
POST /api/auth/set-password
  Body: { password }
  Requires auth. Hashes with bcrypt (cost 12), saves to settings.
  Returns { ok: true }.
```

`GET /api/settings` returns `password_hash` as `"********"` (same as other sensitive fields). A `PUT /api/settings` with `"********"` for `password_hash` leaves it unchanged.

### Frontend changes

**On boot** (`DOMContentLoaded`): call `GET /api/auth/me`.
- Mode `none` or valid session → proceed normally.
- 401 → render login page instead of the normal route.

**Login page (`/#/login`):**
- Form mode: username + password fields, Submit button. `POST /api/auth/login`. On success, re-render the original destination route.
- OIDC mode: single "Sign in" button. Navigates to `GET /api/auth/oidc/start` (full page navigation, not fetch).
- Shows which mode is active based on the 401 response body: `{ mode: "form" | "oidc" }`.

**After login:** redirect to whatever route was requested before the 401, or `/#/` if none.

**Logout:** button in Settings page (visible when auth mode is not `none`). Calls `POST /api/auth/logout`, then reloads the page.

**Settings → Auth tab:**
- Mode selector: None | Form Login | OIDC
- Form mode fields: Username, New Password, Confirm Password + "Set Password" button
- OIDC fields: Provider URL, Client ID, Client Secret, Scopes (pre-filled `openid email profile`), Session duration (days)
- Redirect URI helper: shows the exact URI to register with the provider (non-editable)
- Save button (saves all auth settings except password — password uses the Set Password button)

### API Authentication

> **TODO — needs investigation before Phase 8.**
>
> The current design authenticates the browser SPA via cookie-based sessions. However,
> if the app ever needs to be called programmatically (scripts, other services, future
> mobile clients), cookie auth is impractical. Questions to resolve:
>
> - Should we support API keys (static tokens in `Authorization: Bearer` header)?
> - If so: where are they stored (settings.yaml? DB table?), how are they issued/revoked,
>   and do they carry the same permissions as a browser session?
> - Should API key auth and session auth share the same `require_auth` dependency, or
>   be separate?
> - Does the OIDC mode need a separate machine-to-machine (client_credentials) flow,
>   or is that out of scope for a single-user self-hosted app?
>
> Resolve this before finalising the auth implementation. It may be simplest to defer
> API keys to a later phase and note it in Future Work.

### Building order

Auth is **Phase 8** — implement after all core functionality is working. The app is assumed to run on a trusted local network until then.

Phase 8 steps:
1. Add `python-jose[cryptography]` and `passlib[bcrypt]` to `requirements.txt`
2. Add `auth` section to default settings in `app/settings.py`; auto-generate `session_secret` on startup if empty
3. `app/auth.py` — `require_auth` dependency, JWT helpers, session cookie helpers
4. `app/routes/auth.py` — login, logout, me, set-password, oidc/start, oidc/callback
5. Wire `Depends(require_auth)` onto all existing routers in `main.py`
6. Frontend: boot auth check, login page (form + OIDC variants), logout button in Settings
7. Settings → Auth tab

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
app.include_router(book_links_router, prefix="/api")
app.include_router(sync_router, prefix="/api")

# Serve index.html with Cache-Control: no-cache so browsers always revalidate
# (prevents stale HTML caching the old ?v=N script tag)
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})

# Serve other static assets (CSS, JS) — these can be cached by the browser
app.mount("/static", StaticFiles(directory="static"))

# On startup: init DB, start background tasks
@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(download_monitor())      # polls every 15s
    asyncio.create_task(library_sync_task())   # schedule.library_sync cron
    asyncio.create_task(cache_refresh_task())  # schedule.cache_refresh cron
    asyncio.create_task(auto_search_task())    # schedule.auto_search cron

# GET /healthz
# Runs SELECT 1 against the database. Returns 200 { ok: true } if reachable,
# 503 { ok: false, error: "..." } if not. Used by Docker HEALTHCHECK.
# Must not require authentication or any service configuration to respond.

# GET /api/status
# Returns: { books: int, authors: int, series: int,
#            requests: { requested: int, snatched: int,
#            downloading: int, downloaded: int, merging: int, organizing: int,
#            in_library: int, failed: int } }
```

### Background Tasks

All background tasks use a supervised loop pattern — the outer loop catches any exception, logs it, and continues. Work logic is separated into a `_tick()` helper to keep the supervisor clean:

```python
async def download_monitor():
    while True:
        try:
            await _download_monitor_tick()
        except Exception as e:
            logger.error(f"download_monitor error: {e}", exc_info=True)
        await asyncio.sleep(15)
```

Apply the same pattern to all scheduled tasks. A single run failure never kills the task — it logs and waits until the next scheduled time.

All scheduled tasks use `croniter` (add to requirements.txt) to calculate the next run time from their cron expression in settings:

```python
async def _wait_until_next(cron_expr: str):
    now = datetime.now()
    next_run = croniter(cron_expr, now).get_next(datetime)
    await asyncio.sleep((next_run - now).total_seconds())

async def library_sync_task():
    while True:
        await _wait_until_next((await get_settings())["schedule"]["library_sync"])
        try:
            await sync_library()
        except Exception as e:
            logger.error(f"library_sync_task error: {e}", exc_info=True)
```

All three scheduled tasks (`library_sync_task`, `cache_refresh_task`, `auto_search_task`) follow this exact pattern. None run on startup — they wait for their first scheduled time.

Each scheduled task upserts `task_state` at the start and end of every run:

```python
# On run start:
await db.execute(
    "INSERT OR REPLACE INTO task_state (task, running) VALUES (?, 1)",
    (task_name,)
)
# On run end (success):
await db.execute(
    "INSERT OR REPLACE INTO task_state (task, running, last_run, last_result) VALUES (?, 0, ?, 'ok')",
    (task_name, datetime.utcnow().isoformat())
)
# On run end (error):
await db.execute(
    "INSERT OR REPLACE INTO task_state (task, running, last_run, last_result) VALUES (?, 0, ?, ?)",
    (task_name, datetime.utcnow().isoformat(), f"error: {e}")
)
```

`download_monitor` is continuous and not tracked in `task_state`.

**`_download_monitor_tick()`** — called every 15 seconds
1. Get all requests with status in `[snatched, downloading]`
2. For each, poll the download client (qBittorrent or SABnzbd) using `download.download_id`
3. Update `downloads.status` and `requests.status` in a single transaction
4. On completion (status = downloaded): `asyncio.create_task(_auto_organize(request_id, download_path))`

**`_auto_organize(request_id, path)`** — detached background task (always `asyncio.create_task`, never awaited)

The organize sequence is designed to be **idempotent** — safe to re-run after a partial failure.

1. Read request metadata: title, author, series, series_position, type
2. **Detect multi-file:** if `path` is a directory containing audio files, note `file_count=N`
3. **Merge step** (if `type='audiobook'` AND multi-file AND `settings.merge_multifile_audiobooks`):
   - Set `requests.status = 'merging'`; create `merge_jobs` row with `source_path`, `file_count`
   - Run `_merge_to_m4b(source_dir, tmp_path, title, author)` (see M4B Merge below)
   - On merge failure: set `merge_jobs.merge_error=...`, `requests.status='failed'`; return
   - On success: set `merge_jobs.merged_path=tmp_path`; use merged file as source for step 4
4. Set `requests.status = 'organizing'`
5. Compute destination path from settings (separate_type_dirs, prefixes)
6. Move file to destination: if source exists → move; if already at destination → skip (idempotent); if neither → `requests.status='failed'`, return
7. Set `merge_jobs.organized_path` (if merge job exists)
8. Trigger ABS library scan
9. Poll ABS for match (title + author + type) — up to 10 retries with 5s delay
10. On match: `UPDATE requests SET status='in_library', abs_id=?`; upsert `book_links`; delete any `merge_jobs` row for this request (merge details no longer needed once in library)
11. On retries exhausted: `UPDATE requests SET status='failed'`; log reason

`POST /api/requests/{id}/organize` (manual retry) calls `_auto_organize(request_id, path)` as a new task, where `path` is the body param if supplied, otherwise the path from the most recent `downloads` record. Idempotency in step 6 handles the already-moved case.

### M4B Merge Algorithm

`_merge_to_m4b(source_dir, output_path, title, author)` — uses `ffmpeg` + `ffprobe` (both required in the Docker image).

```
1. Collect all audio files in source_dir, sorted by filename (natural/numeric sort)
2. For each file, run ffprobe to get duration in seconds (ffprobe -v quiet -show_entries
   format=duration -of csv=p=0 <file>)
3. Build an ffmetadata chapter file:
     [CHAPTER]
     TIMEBASE=1/1000
     START=<cumulative_ms>
     END=<cumulative_ms + duration_ms>
     title=<filename without extension>
   One chapter per source file, using the filename as chapter title.
4. Concatenate + re-encode in one ffmpeg pass:
     ffmpeg -f concat -safe 0 -i filelist.txt \
            -i chapters.ffmetadata \
            -map_metadata 1 \
            -map 0:a \
            -c:a aac -b:a 128k \
            -metadata title="<title>" \
            -metadata artist="<author>" \
            <output_path>.m4b
5. On non-zero exit code: raise with stderr as merge_error
6. Clean up temp filelist and ffmetadata files
```

**Dockerfile requirement:**
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*
```

**`library_sync_task()`** — cron schedule: `schedule.library_sync`
Calls `sync_library()`. Does not run on startup.
After ingesting each new ABS item, immediately attempts HC linking inline (see HC Linking below).
Manual trigger: `POST /api/sync/library`.

**`cache_refresh_task()`** — cron schedule: `schedule.cache_refresh`
Refreshes stale HC data for all linked entities (books, series, authors). Time-sliced to 1 hour max — stops when the hour is up and continues with the next-oldest entries the following night.
Priority order: entries with `expires_at` closest to now (or already expired) first.
Cache TTL: 14 days from `created_at`. Entries are overwritten on refresh, not deleted.
On cache miss at read time (page load): fetch live from HC, store result immediately — don't wait for the nightly run.
At the start of each run, purge orphaned/old entries:
```sql
DELETE FROM metadata_cache WHERE expires_at < datetime('now', '-7 days')
```
This retains expired entries for 7 days after expiry (21 days total) before removing them.
Manual trigger: `POST /api/sync/cache-refresh`.

**`auto_search_task()`** — cron schedule: `schedule.auto_search`
If `schedule.auto_search` is empty, the task is effectively disabled — the scheduler loop skips it. Leave the field blank in settings to disable auto-search globally.
For each `requested` item (status = 'requested'), trigger a Prowlarr search.
On finding a result and triggering a download: send a Pushover notification via `notify_snatched()`.
Notification is fire-and-forget — failure to notify must never block the download.

### API Endpoints

All routes return JSON. All IDs are UUIDs (TEXT in SQLite).

#### Books (`app/routes/books.py`)

```
POST   /api/books
  Body: { title, author, cover_url?, series?, series_position?,
          metadata_source?, metadata_id?, metadata_url?,
          requests: [{type, narrator?}] }
  Creates the book (if not duplicate by title+author), then calls
  _create_request(book_id, type, narrator) for each entry in requests[].
  Returns: book detail with _created_requests, _skipped_requests counts

GET    /api/books?q=...&sort=title&dir=asc&limit=50&offset=0
  q: filter by title or author (server-side LIKE match)
  sort: title | author | created_at (default: title)
  Returns: { items: [{...}], total: int, limit: int, offset: int }

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
  "requests": [{"id": "uuid", "type": "audiobook", "status": "downloading", "narrator": "..."}],
  "library_formats": [{"type": "audiobook", "narrator": "..."}],
  "link": {"abs_id": "...", "hardcover_id": "..."}
  // library_formats: derived from ABS via abs_id (ground truth for what is physically present)
  // requests: from the requests table (what is pending/in-progress/in_library)
}
```

#### Authors & Series (`app/routes/books.py`)

```
GET    /api/authors?q=...&sort=name&dir=asc&limit=50&offset=0
  q: filter by name
  Returns: { items: [{ id, name, book_count, link: {hardcover_author_id?} }], total: int, limit: int, offset: int }

GET    /api/authors/{author_id}/books
  Returns: [book detail shape]

GET    /api/series?q=...&sort=name&dir=asc&limit=50&offset=0
  q: filter by name
  Returns: { items: [{ id, name, book_count, link: {hardcover_series_id?} }], total: int, limit: int, offset: int }

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
GET    /api/search/metadata?q=...&series_id=...
  Search Hardcover, annotate results with local data:
    - Check book_links for hardcover_id match → set book_id, in_library
    - Check requests for existing requests by title+author → set existing_requests
    - Fetch ABS item for in_library books → set library_formats (for dupe prevention)
  Optional series_id: when present, sort that series first in each result's series array.
  Returns: { results: [search result shape] }

GET    /api/search/advanced?title=...&author=...&series=...&series_id=...
  Same annotation and series_id behaviour as above.
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
  "series": [{"id": "local_uuid_or_null", "hardcover_series_id": "...", "name": "...", "position": "7"}],
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

`series` is always an array sorted by relevance — context series first, then by HC `users_count` descending.
Frontend renders only `series[0]` on cards. Full array available for detail views.

#### Requests (`app/routes/requests.py`)

```
POST   /api/requests
  Body: { book_id, type, narrator? }
  Calls _create_request(book_id, type, narrator).
  Returns: request detail, or { skipped: true } if dedup rule matched

GET    /api/requests?status=...&type=...&book_id=...&q=...&sort=created_at&dir=desc&limit=50&offset=0
  q: filter by book title or author
  Returns: { items: [request detail], total: int, limit: int, offset: int }

GET    /api/requests/{id}
  Returns: request detail with download history

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
  Body: { path?: string }
  Manually trigger organize. If path is provided, use it instead of the stored download path.
  Returns: { ok: true }

POST   /api/requests/sync-library
  For all non-in_library requests, check ABS; promote if found.
  Returns: { ok: true, updated: N }
```

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
  Validates that path values (output_dir, download_dir) exist in the container.
  Validates cron expressions under schedule.*: attempt croniter(value, datetime.now()) and return
  400 { error: "Invalid cron expression: <field>" } if it raises. Returns { ok: true } on success.

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
  Reads from task_state table. Returns:
  { library_sync:  { running, last_run, last_result },
    cache_refresh: { running, last_run, last_result },
    auto_search:   { running, last_run, last_result } }
  All fields present even if task has never run (running: false, last_run: null, last_result: null).
  Persists across restarts.
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

### Hardcover API Reference

Endpoint: `POST https://api.hardcover.app/v1/graphql`
Auth: `Authorization: Bearer <api_key>`
Rate limit: 60 requests/minute. Handle 429 with exponential backoff (start 2s, double, cap 60s).

#### Search (Typesense index — fast, returns raw JSON documents)

```graphql
query Search($q: String!, $type: String!) {
  search(query: $q, query_type: $type, per_page: 5) {
    results  # jsonb: { found: Int, hits: [{ document: { ... } }] }
  }
}
```

Supported `query_type` values: `"Book"`, `"author"`, `"series"`, `"user"`, `"list"`, `"publisher"`, `"character"`, `"all"`.

Search document shapes vary by type. For books: `id`, `title`, `slug`, `contributions`/`cached_contributors` (author list), `book_series` (series list). For authors: `id`, `name`, `slug`, `books_count`. For series: `id`, `name`, `slug`, `books_count`.

Name matching: fetch up to 5 candidates and rank client-side with `rapidfuzz.fuzz.token_sort_ratio`. For authors/series, prefer results where `state == "active"` and `canonical_id == null` (canonical records over aliases/duplicates).

#### Direct lookup by ID (Hasura/Postgres — strongly typed, supports relationship traversal)

```graphql
# Book by numeric HC ID
query { books_by_pk(id: 12345) {
  id slug title subtitle description release_year pages audio_seconds
  rating ratings_count users_count
  contributions { author { id name slug } }
  book_series(order_by: { position: asc_nulls_last }) {
    position featured compilation
    series { id name slug }
  }
}}

# Author by numeric HC ID
query { authors_by_pk(id: 456) {
  id name slug bio books_count state canonical_id
  contributions(limit: 25, order_by: { created_at: desc }) {
    book { id slug title release_year }
  }
}}

# Series by numeric HC ID — primary path for missing-books detection
query { series_by_pk(id: 789) {
  id name slug description books_count primary_books_count is_completed
  book_series(order_by: { position: asc_nulls_last }) {
    position featured compilation details
    book { id slug title release_year rating cached_contributors }
  }
}}
```

`book_series.position` is `float8` (allows 1.5 for novellas between whole-number entries). `featured` distinguishes primary entries from companions/spinoffs. `compilation` marks omnibus volumes.

#### `cache_refresh` HC linking strategy

**Primary path — book search carries everything:**
When `_link_to_hardcover` finds a match, the HC book search result includes `contributions` (author IDs) and `book_series` (series IDs). These are extracted and stored immediately in `author_links.hardcover_author_id` and `series_links.hardcover_series_id`. This means a single HC search call links the book, its authors, and its series simultaneously.

**Catch-up passes — explicit but rare:**
After the book pass completes, two additional passes handle authors/series that still lack HC IDs (edge cases: HC returned no contributor data, or a series/author was created via a path that didn't go through a book search):

- **Author catch-up:** search HC with `query_type: "author"` for each author with no `hardcover_author_id`
- **Series catch-up:** search HC with `query_type: "series"` for each series with no `hardcover_series_id`

These catch-up passes are defensive. In normal operation (after a full book link pass) there should be few or zero items to process.

#### HC matching rules (empirically tuned)

**Title scoring — `_title_score(local, hc)`:**
- Normalise both sides: `&` → `and`, lowercase
- Strip HC subtitle (everything after first `:`) and score against that too
- Take `max(full_score, stripped_score)` using `token_sort_ratio`
- Accept if `t_score >= 90`
- Rationale: HC often appends `: A Novel` / `: Book N of …` etc. Stripping prevents false negatives. `&` vs `and` is common (e.g. "Angels & Demons" on HC vs "Angels and Demons" locally).

**Author scoring — `_author_score(a, b)`:**
- Take `max(token_sort_ratio(a, b), ratio(norm(a), norm(b)))` where `norm` strips all spaces and periods
- This handles initials: "V. E. Schwab" ↔ "V.E. Schwab" both normalise to "veschwab"
- For multi-author books, score is `max` across all local authors × all HC contributors
- Accept if `a_score >= 85`
- Rationale: `token_sort_ratio` alone fails on initials because "V." and "E." are separate tokens vs "V.E." as one token.

**Search depth:** `per_page: 15` — HC Typesense sometimes ranks the correct book 6th–10th (e.g. popular titles with many editions). Confirmed `_ilike` WHERE queries are blocked server-side; Typesense search is the only HC search path.

**Conflict handling:**
- Books: if HC book ID already claimed by another local book, log warning and skip (two ABS items for same book, e.g. audiobook + ebook as separate entries)
- Authors: `_set_hc_author_id()` checks before UPDATE — same author entered with slightly different name (e.g. "James S. A. Corey" vs "James S.A. Corey") both match same HC author; first wins, second is skipped and logged

**Future: missing books detection** (cache_refresh Phase 4+):
For series with a `hardcover_series_id`, call `series_by_pk` to get all positions. Compare against `book_series` positions we own. Surface gaps as missing books. Cache result in `metadata_cache` with 14-day TTL.

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
```
┌──────────────────────────────────────┐
│ nav (sticky top, height 48px)        │
├──────────────────────────────────────┤
│                                      │
│  main (max-width 1100px, centred)   │
│                                      │
└──────────────────────────────────────┘
```

Nav items: [logo → home] | Library ▾ | Requests | Downloads | Dashboard | Settings

The logo (left side of nav) navigates to `/#/`. There is no "Search" nav item — the home page is search.

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
function render() { /* match hash → call handler → set #app.innerHTML; fallback to 404 if no match */ }
window.addEventListener('hashchange', render);
window.addEventListener('DOMContentLoaded', render);
```

Route params: `/library/series/:id` parsed into `{ id: "..." }`.

If no route matches, render a centred "Page not found." message in `--text-dim`. No retry link.

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
// Renders a paginated table with server-side sort, filter, and infinite scroll.
// config: {
//   container: Element,
//   headers: [{label, key, sortable?, style?}],
//   fetchFn: (params) => Promise<{items, total}>  // called by renderTable on state changes
//   renderRow: (row) => html string,
//   stateKey: string   // URL param prefix, e.g. "books" → ?books_sort=title&books_dir=asc&books_q=...
// }
//
// Sort/filter/pagination state lives in URL hash params (survives navigation and refresh):
//   ?{stateKey}_sort={key}&{stateKey}_dir=asc|desc&{stateKey}_q={text}&{stateKey}_offset={n}
//
// On init: reads state from URL params, calls fetchFn, renders first page.
// On column header click: reset offset to 0, update URL params, call fetchFn, replace rows.
// On filter input: debounced 200ms, reset offset to 0, update URL params, call fetchFn, replace rows.
// On scroll to bottom (IntersectionObserver on last row): increment offset, call fetchFn, append rows.
// Infinite scroll stops when items.length < limit (last page reached).
// fetchFn receives { q, sort, dir, limit: 50, offset } — maps directly to API params.
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

// Inline confirmation: click once → warning state → click again → action
// State is stored as data-confirming on the button element — not in a JS variable.
// Re-renders naturally reset confirm state (user navigated away = confirmation cancelled).
// Multiple buttons can be in confirm state simultaneously — each manages its own state.
// Usage: btn.onclick = () => confirmAction(btn, 'Delete?', () => doDelete())
function confirmAction(btn, confirmText, action) { ... }

// Renders a stats header card for author/series detail pages
function renderDetailStats(name, stats) { ... }
// stats: { inLibrary: N, total: N, requested: N, missing: N, loadingMissing: bool }
```

**Loading and error states (applies to all pages):**

Every page that fetches data follows this pattern — no exceptions:

- **Loading:** render `ICON_SPINNER` centred in the content area while the fetch is in flight. No partial renders.
- **Error:** on any thrown error from `api()`, render a centred message: "Failed to load. [Retry]" where Retry re-runs the same fetch. Use `--text-dim` for the message, `--accent` for the link.

These are the only two states needed. Implement as two small helper functions:

```javascript
function renderLoading(container) {
  container.innerHTML = `<div class="state-loading">${ICON_SPINNER}</div>`;
}

function renderError(container, retryFn) {
  container.innerHTML = `<div class="state-error">Failed to load. <a href="#" class="retry">Retry</a></div>`;
  container.querySelector('.retry').onclick = (e) => { e.preventDefault(); retryFn(); };
}
```

Every route handler calls `renderLoading(app)` before its first `api()` call, then `renderError(app, render)` in the catch block.

**`expandRequestForm(slot, result, onSuccess = null)`:**
- Shows format selection: Audiobook button and Ebook button
- For each format, checks `result.library_formats` (what ABS has) and `result.existing_requests` (what's in flight):
  - Format not present anywhere: button enabled, normal label
  - Format in `library_formats`: button label shows "have (Narrator Name)" if narrator known, or "have" if not — button remains **enabled** so a different narrator can be requested
  - Format in `existing_requests` with non-failed status: button disabled, label shows current status (e.g. "downloading")
- When Audiobook is selected, a narrator input appears below the format buttons:
  - Placeholder: "Narrator (optional)"
  - Optional — leaving blank submits a null narrator
  - Not shown when only Ebook is selected
- The "already have it" check for the submit button is narrator-aware: if the entered narrator matches an existing `in_library` request narrator (case-insensitive), that format is blocked with "already have this narrator"
- On submit: `POST /api/books` (creates book + requests), then `POST /api/requests` if book already existed
- On success: call `onSuccess(createdBook, result, selectedTypes)` or navigate to book detail

### Frontend Routes

```
/#/                          Home / Search
/#/library/books             Books list (table/grid, filterable)
/#/library/authors           Authors list (table/grid)
/#/library/authors/:id       Author detail
/#/library/series            Series list (table/grid)
/#/library/series/:id        Series detail
/#/library/book?book_id=...  Book detail
/#/requests                  Requests list (filterable by status/type)
/#/requests/:id              Request detail
/#/downloads                 Active downloads
/#/dashboard                 Stats dashboard
/#/settings                  Settings
```

### Key Page Behaviours

**Home / Search page (`/#/`):**

The home page is the search page. On first load (no query), it shows only the search input centred vertically in the content area — nothing else.

```
┌──────────────────────────────────────────────────┐
│  nav                                             │
├──────────────────────────────────────────────────┤
│                                                  │
│                                                  │
│    ┌──────────────────────────────────┬──┐       │
│    │  Search for a book...            │⚙ │       │
│    └──────────────────────────────────┴──┘       │
│                                                  │
│                                                  │
└──────────────────────────────────────────────────┘
```

The search input is wider than standard (max-width ~600px), rounded (`border-radius: 24px`), and centred both horizontally and vertically (flexbox column, justify-content: center on the page). It stands alone with generous whitespace above and below — no heading, no subtext.

The `⚙` (or sliders/filter icon) sits inside the right edge of the input as an icon button. Clicking it expands the advanced fields inline below the input:

```
┌──────────────────────────────────────┬──┐
│  Search...                           │⚙ │  ← icon is highlighted/active
└──────────────────────────────────────┴──┘
┌──────────────────┐ ┌───────────────┐
│  Title...        │ │  Author...    │
└──────────────────┘ └───────────────┘
┌──────────────────┐
│  Series...       │
└──────────────────┘
```

Advanced fields appear with a smooth CSS transition (height/opacity). When advanced is open, the main input is used as the title field — they are the same input. Author and series fields appear below. The advanced icon is visually active (accent colour) while expanded.

Search state is persisted in URL hash params so navigation and back/forward work correctly:
- `/#/?q=dune` — basic search
- `/#/?q=dune&author=herbert&advanced=1` — advanced search (expanded)

On route render: read params, pre-fill inputs, re-run search automatically if `q` is present. `advanced=1` expands the advanced fields on load.

A clear button (`✕`) appears inside the search input (right side, inside the border, left of the advanced icon) whenever any input has a value. Clicking it clears all fields, removes all search params from the URL, hides results, and returns the page to its initial centred state. The clear button is hidden when all inputs are empty.

Submitting (Enter or a search icon button): calls the appropriate API endpoint:
- Advanced closed: `GET /api/search/metadata?q=...`
- Advanced open: `GET /api/search/advanced?title=...&author=...&series=...`

Results render below the search input, pushing it toward the top of the page. The page no longer vertically centres the input once results are shown (input stays at top, results fill below).

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
- If response includes `truncated: true`, show a note below the missing books list: "Showing first 50 entries — this series is too large to display in full."

**Book detail (`/#/library/book?book_id=...`):**
- Shows book metadata (from DB + Hardcover if linked)
- Shows all requests with expandable dropdown
- Request dropdown has: Search Prowlarr button + Delete Request button
- For `failed` requests that passed through `merging` or `organizing`: also shows "Retry Organize" button
  - Clicking opens a text input pre-filled with the last known path from the downloads record
  - User can correct the path before submitting
  - Submits `POST /api/requests/{id}/organize` with the (possibly corrected) path
- Delete: click once → "Click again to confirm" (orange) → click again → deleted, removed from DOM

**Book detail — ABS linking section:**

Appears below the book metadata. Three states:

1. **Linked** — shows the current ABS item: title, cover thumbnail, format badges (audiobook/ebook). An "Unlink" button calls `DELETE /api/metadata-links/{id}` and transitions to state 2 or 3.

2. **Unlinked, potential matches found** — on page load, if `book_links.abs_id` is null, automatically calls `GET /api/abs/search?title=...&author=...` using the book's title and primary author. Renders each candidate as a row: cover thumbnail, title, author, format badges, and a "Link" button. Clicking Link calls `POST /api/metadata-links` with `{ book_id, abs_id }` and transitions to state 1.

3. **Unlinked, no matches** — if the auto-search returns zero results, shows a manual search input ("Search AudiobookShelf…") that calls `GET /api/abs/search?title=...` on submit. Results render the same candidate row format as state 2. A "No match" label is shown if the manual search also returns nothing.

**Requests list (`/#/requests`):**

Filterable table of all requests. Columns: Book title, Author, Type (audiobook/ebook icon), Status (badge), Narrator (if set), Created date.

Filter controls above the table:
- Status dropdown: All | requested | snatched | downloading | organizing | in_library | failed
- Type toggle: All | Audiobook | Ebook

URL hash params carry filter state (same `renderTable` pattern):
`?requests_status=failed&requests_type=audiobook`

The Dashboard `failed` count card links to `/#/requests?requests_status=failed`.

Empty state per filter:
- No filter active: "No requests yet. [Search for a book] to get started."
- Status filter active: "No [status] requests." (no action link)

Row actions (inline, per row): Delete (with confirm pattern). For `failed` requests: also a "Retry" button that calls `POST /api/requests/{id}/organize` directly if the request has a download path, otherwise navigates to request detail.

**Request detail (`/#/requests/:id`):**
- Full request info, status history
- Prowlarr search results with one-click download
- Download history

**Downloads (`/#/downloads`):**
- Polls every 5 seconds
- Shows speed, ETA, progress bar for each active download

**First-run banner:**

On every page load, the frontend checks `GET /api/settings`. If `audiobookshelf.url` is empty, render a yellow banner directly below the nav (not dismissible):

```
⚠ AudiobookShelf is not configured. Go to Settings to get started.
```

"Go to Settings" links to `/#/settings`. The banner disappears automatically once the ABS URL is saved (the next settings fetch will see it populated). No other services block the banner — ABS is the only required one.

**Empty states:**

Every list page renders a centred empty state when its data returns zero rows. Style: dimmed text (`--text-dim`), no icon, action links use the standard `--accent` colour.

| Page | Message | Action link |
|------|---------|-------------|
| Books | "Your library is empty." | "Sync from AudiobookShelf" → triggers `POST /api/sync/library`; or "Search for a book" → `/#/` |
| Authors | "No authors yet. Authors are added automatically when books are synced." | "Sync library" → triggers `POST /api/sync/library` |
| Series | "No series yet. Series are added automatically when books with series data are synced." | "Sync library" → triggers `POST /api/sync/library` |
| Requests | "No requests yet." | "Search for a book" → `/#/` |
| Downloads | "Nothing downloading right now." | — (no action; this is a normal state) |

The Books empty state shows both links (sync existing library OR search for something new) since a new user might not have ABS set up yet.

After a sync is triggered from an empty state, show a toast: "Library sync started — check back in a moment."

**Dashboard (`/#/dashboard`):**
- Calls `GET /api/status` and `GET /api/sync/status` on load
- Shows library totals (books, authors, series) as large stat numbers in a row of cards
- `failed` count card uses `--red` accent and links to `/#/requests?requests_status=failed`
- Shows a third row: scheduled task status for `library_sync`, `cache_refresh`, `auto_search`.
  Each card shows: task name, `running` indicator (spinner if true), `last_run` timestamp, `last_result` (green "ok" or red "error: ..."). If never run: "Never run" in `--text-dim`.
- No auto-refresh — user refreshes manually or navigates away and back

**Settings (`/#/settings`):**
- Split into tabs: General | ABS | Prowlarr | qBittorrent | SABnzbd | Hardcover | Pushover | Sync
- Each tab has its own Save button — saves only that section (`PUT /api/settings` with the tab's key)
- ABS, Prowlarr, qBittorrent, SABnzbd tabs each have a Test Connection button (calls the relevant `/api/settings/test/*` endpoint)
- Sensitive fields (api_key, password) are returned as `"********"` by GET; if PUT receives `"********"` for a sensitive field, the backend leaves the existing value unchanged
- On save: show inline success/error feedback next to the Save button
- **Tasks tab:** shows cron schedule inputs for `library_sync`, `cache_refresh`, `auto_search` with a single Save button. Leaving a cron field blank disables that task — the scheduler skips it. The UI shows "Disabled" for tasks with an empty schedule. Below the form, shows current task state (last run, last result) read from `GET /api/sync/status`. Manual trigger buttons: "Run now" for each task — calls `POST /api/sync/library` or `POST /api/sync/cache-refresh`. After triggering, button disables and shows "Running…" until the next status poll confirms `running: false`.

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

**Deduplication key: `(book_id, type, narrator)`**

Narrator is part of the request identity. This allows requesting the same audiobook with a different narrator (e.g. you have narrator A in library, you want narrator B).

A request is **skipped** if a row already exists in `requests` for the same `(book_id, type, narrator)` in any non-failed status. Rules:

- `narrator` comparison is case-insensitive string match
- `NULL` narrator matches `NULL` narrator only — a null-narrator request and a named-narrator request are considered different
- `failed` requests do NOT block re-requesting — create a new request (the failed one can be deleted)
- `in_library` requests DO block re-requesting the same narrator — you already have it

This logic lives in one place: **`_create_request(book_id, type, narrator)`** in `app/routes/requests.py`, called by both `POST /api/books` and `POST /api/requests`.

```
_create_request(book_id, type, narrator) -> (request_row | None)
  1. Query: SELECT id FROM requests WHERE book_id=? AND type=? AND
            (narrator = ? OR (narrator IS NULL AND ? IS NULL))
            AND status != 'failed'
  2. If match found: return None (caller counts as skipped)
  3. If no match: INSERT new request with status='requested', return row
```

Returns `None` on skip, the new request row on creation. Callers must not duplicate this check.

**Frontend narrator-awareness:**

`library_formats` check must be narrator-aware. Having narrator A `in_library` shows as "have (Narrator A)" next to the audiobook button but does NOT disable requesting a different narrator. The request form should allow specifying a narrator, and the "already have it" check compares against the specific narrator entered.

`library_formats` is always derived from ABS directly via `audiobookshelf.get_item_by_id(abs_id)`.
For books with no `abs_id`, `library_formats` is an empty array.
This applies everywhere: search results, book list, book detail — same derivation, same field name.

Do NOT use request status to infer library presence — requests can be stale.
Do NOT use a `formats` field — always use `library_formats` (what ABS has) alongside `requests` (what is in flight).

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
5. Filter: skip if `hardcover_id` is in our `book_links`, OR if the position in this series matches a book we already have
6. Sort numerically: use `float(position)` where possible; on `ValueError` treat as infinity (sorts last)
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

Build in this order. Each phase should be working before starting the next. Write the tests for a phase before moving on to the next.

### Phase 0: CI Setup
1. `.github/workflows/test.yml` — run pytest on push/PR to main
2. `.github/workflows/docker.yml` — build + push to ghcr.io on version tags
3. `requirements-dev.txt` — pytest, pytest-asyncio, pytest-httpx
4. `tests/conftest.py` — DB fixture (tmp_path), ASGI test client fixture
5. `tests/test_database.py` — smoke test: `init_db()` runs, correct `user_version`, all tables present

### Phase 1: Foundation
1. `Dockerfile` and `requirements.txt`

**`requirements.txt`:**
```
fastapi
uvicorn[standard]
aiosqlite
httpx
python-multipart
pyyaml
rapidfuzz
croniter
```

**`Dockerfile`:**
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8743
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8743/healthz || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8743"]
```

No version-pinning in requirements.txt during development — pin to known-good versions before first stable release.
2. `app/database.py` — `SCHEMA_V1` constant, `_run_migrations()`, `init_db()`
3. `app/settings.py` — read/write settings YAML
4. `app/main.py` — bare FastAPI app, static file serving, DB init on startup
5. `static/index.html` — HTML shell with nav, `<div id="app">`, script tag
6. `static/style.css` — full design system (variables, cards, badges, buttons, layout, tables, grid)
7. `static/app.js` — router, api(), toast(), all icon constants, shared render functions skeleton, home/search page

**Tests:** `tests/test_settings.py` — get_settings returns defaults on missing file, save + reload round-trip, concurrent saves don't corrupt. `tests/test_routes/test_main.py` — `GET /healthz` returns 200, `GET /api/status` returns expected shape.

### Phase 2: Settings & ABS
8. `app/services/audiobookshelf.py` — all methods
9. `app/routes/settings.py` — GET/PUT settings, 4 connection test endpoints
10. Settings page in frontend — form groups, test buttons, save

**Tests:** `tests/test_services/test_audiobookshelf.py` — each public method with mocked httpx responses (success + error cases). `tests/test_routes/test_settings.py` — GET returns current settings, PUT persists changes, connection test endpoints return correct structure on mock success/failure.

### Phase 3: Library Sync
11. `app/services/library_sync.py` — sync_library(), helpers
12. `app/routes/books.py` (partial) — GET /api/books, GET /api/authors, GET /api/series
13. Library pages: Books list, Authors list, Series list (table + grid views)

**Tests:** `tests/test_services/test_library_sync.py` — sync inserts books/authors/series correctly, re-sync updates without duplicating, author_links/series_links use INSERT OR IGNORE + UPDATE (never INSERT OR REPLACE). `tests/test_routes/test_books.py` — list endpoints return correct shape, pagination, empty results.

### Phase 4: Search & Requests
14. `app/services/book_search.py` — all search methods
15. `app/routes/books.py` (complete) — search endpoints, series missing, book detail
16. Search page frontend — quick + advanced, in-place request success
17. `app/routes/requests.py` — CRUD, sync-library
18. Requests list page (`/#/requests`) — filterable table, row actions
19. Request-related UI on book cards and detail pages

**Tests:** `tests/test_services/test_book_search.py` — search, series lookup, best-match selection logic (mocked Hardcover). `tests/test_routes/test_requests.py` — `_create_request()` deduplication: new request created, duplicate blocked, narrator-differentiated requests both allowed, failed status allows re-request, DELETE removes row (not sets cancelled).

### Phase 5: Downloads
20. `app/routes/requests.py` — search-indexers, download, organize endpoints
21. `app/routes/downloads.py`
22. `app/main.py` — download_monitor background task
23. Request detail page, Downloads page

**Tests:** `tests/test_routes/test_downloads.py` — list endpoint shape, status filtering. `tests/test_routes/test_requests.py` (additions) — search-indexers returns mocked results, download endpoint creates download row, organize endpoint transitions status correctly.

### Phase 6: Detail Pages
24. `GET /api/book/detail?book_id=...&abs_id=...` endpoint
25. Book detail page — metadata, ABS linking, request management
26. Author detail page — books, stats
27. Series detail page — books, completion, missing books (async loading)
28. `app/routes/book_links.py`
29. `app/routes/sync.py`

**Tests:** `tests/test_routes/test_books.py` (additions) — book detail returns correct shape, 404 on unknown id, series missing-books list excludes already-owned positions. `tests/test_routes/test_book_links.py` — link/unlink round-trip.

### Phase 7: Polish
30. Dashboard stats page (`/#/dashboard`)
31. Active download polling
32. Library sync progress (task_state display in UI)
33. Mobile/responsive CSS fixes

**Tests:** `tests/test_routes/test_main.py` (additions) — `/api/status` counts match seeded data.

### Phase 8: Authentication
34. `python-jose[cryptography]` and `passlib[bcrypt]` in `requirements.txt`
35. `auth.session_secret` auto-generated in `app/settings.py` startup
36. `app/auth.py` — `require_auth` dependency, JWT + cookie helpers
37. `app/routes/auth.py` — login, logout, me, set-password, OIDC endpoints
38. Wire `Depends(require_auth)` onto all routers in `main.py`
39. Frontend: boot auth check, login page (form + OIDC), logout in Settings
40. Settings → Auth tab

**Tests:** `tests/test_routes/test_auth.py` — login with correct password returns token cookie, wrong password returns 401, protected endpoint returns 401 without cookie, returns 200 with valid cookie, logout clears cookie.

---

## Testing

### Goals

- Catch regressions in business logic (request deduplication, library sync merging, download state transitions)
- Validate API contract (status codes, response shapes) without running a real ABS/Hardcover/Prowlarr
- Run fast enough to execute on every push (target: under 60 seconds)

### Stack

Add to `requirements.txt` (dev dependencies — keep in a separate `requirements-dev.txt`):

```
pytest
pytest-asyncio
pytest-httpx
```

`pytest-httpx` intercepts `httpx.AsyncClient` calls so external services are never hit in tests.

### Test Structure

```
tests/
├── conftest.py          # shared fixtures: test DB, test settings, app client
├── test_database.py     # migration correctness, schema integrity
├── test_settings.py     # get_settings / save_settings round-trips
├── test_routes/
│   ├── test_books.py    # GET /api/books, /api/authors, /api/series, search
│   ├── test_requests.py # request CRUD, deduplication logic
│   └── test_downloads.py
└── test_services/
    ├── test_audiobookshelf.py  # mocked HTTP responses
    ├── test_book_search.py     # mocked Hardcover responses
    └── test_library_sync.py   # sync logic against test DB
```

### Fixtures (`tests/conftest.py`)

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
import aiosqlite

@pytest_asyncio.fixture
async def db(tmp_path):
    """In-memory SQLite DB, migrations applied."""
    db_path = tmp_path / "test.db"
    import os; os.environ["DATA_DIR"] = str(tmp_path)
    await init_db()
    yield db_path

@pytest_asyncio.fixture
async def client(db):
    """ASGI test client with real routes, isolated DB."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

Use `tmp_path` so each test gets an isolated database — no shared state between tests.

### What to Test Per Layer

**Routes** — test the HTTP contract: correct status codes, required fields in response JSON, error cases (404 when book not found, 409 when request already exists). Do not test internal service logic through route tests.

**Services** — test business logic directly. Use `pytest-httpx` to mock external HTTP calls:
```python
async def test_search_returns_best_match(httpx_mock):
    httpx_mock.add_response(json={"data": {"books": [...]}})
    svc = BookSearchService(settings)
    results = await svc.search("Dune")
    assert results[0]["title"] == "Dune"
```

**Database / migrations** — assert that `PRAGMA user_version` is correct after `init_db()`, and that all expected tables exist.

**Deduplication** — `_create_request()` is the highest-value test target. Cover: new request created, duplicate blocked, narrator-differentiated requests allowed, failed requests allow re-request.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a single file
pytest tests/test_routes/test_requests.py -v
```

Tests must pass against a clean `tmp_path` database — never depend on `./data/` existing.

---

## CI/CD

### GitHub Actions — Test CI

File: `.github/workflows/test.yml`

Runs on every push and pull request targeting `main`. Fails the check if any test fails.

```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --tb=short
```

No Docker build in the test job — running pytest directly against the source tree is faster and sufficient.

### GitHub Actions — Docker Image Build

File: `.github/workflows/docker.yml`

Builds and pushes a Docker image to GitHub Container Registry (`ghcr.io`) on version tag pushes only (e.g. `v1.2.0`). To release:

```bash
git tag v1.2.0
git push --tags
```

This produces `ghcr.io/<owner>/athenaeum:v1.2.0` and `ghcr.io/<owner>/athenaeum:latest`.

```yaml
name: Docker

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

`GITHUB_TOKEN` is automatically available — no extra secrets needed for GHCR.

GitHub Actions cache (`type=gha`) speeds up repeated builds significantly by caching Docker layers.

### Building Order

Each phase in the Building Order section above includes a **Tests** line specifying exactly what to write before moving on. Phase 0 establishes CI so every subsequent phase starts with a green pipeline.

---

## Future Work

Features deliberately deferred — not in scope for initial build but worth implementing later:

- **Bulk actions on Requests list** — checkbox selection per row, bulk toolbar for monitor/unmonitor/delete. Most useful for clearing a batch of failed requests or monitoring a large import.

- **End-to-end UI tests (Playwright)** — browser-level smoke tests against a running app instance: home page renders, nav routes work, theme toggle switches `html` class, Library dropdown opens, bottom nav visible at mobile viewport. Run in a separate `e2e.yml` workflow (start uvicorn, wait for ready, run Playwright headless, teardown). Tests live in `tests/e2e/`.

---

## What Went Wrong in BookOrganizeClaude (Learn From This)

- **Code rot from iteration:** Logic was spread between routes, main.py, and services with duplication.
  Keep each concern in ONE place.

- **Schema denormalisation:** Early versions had author/series as strings in books table.
  We normalised later, which required rewriting dozens of queries. Start normalised.

- **Inconsistent icons:** Some pages used emoji, some used SVG, some used text.
  Define ALL icons as constants at the top of app.js and use them everywhere.

- **Search vs series endpoint returning different editions:** Hardcover's `series_by_pk`
  returns unpopular editions while `books` search returns popular ones. The per-book
  title search workaround was correct at time of writing — but before implementing,
  research whether the Hardcover API now supports batching or a richer series query.

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

**`docker-compose.yml`:**
```yaml
services:
  athenaeum:
    build: .
    ports:
      - "8743:8743"
    volumes:
      - ./data:/data
      - /path/to/output:/output  # Replace with your actual library path
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8743/healthz"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
```

**`.gitignore`:**
```
data/
*.pyc
__pycache__/
venv/
.env
```

`data/` contains `settings.yaml` (real API keys) and `athenaeum.db`. Never commit it.

**Backups:** Before any upgrade, back up `./data/` — it contains both the database and your API keys. A simple `cp -r ./data ./data.bak` before `docker compose up -d --build` is sufficient.

```bash
# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f

# Rebuild after any change
docker compose up -d --build
```

Port: **8743** (different from BookOrganizeClaude's 8742, so both can run simultaneously)

**Security note:** No authentication is implemented. Athenaeum is designed for self-hosted use on a trusted network. Do not expose port 8743 to the public internet.

