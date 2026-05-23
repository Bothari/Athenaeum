# Athenaeum — Claude Code Instructions

## Project Overview

Athenaeum is a self-hosted book management app. Full specification is in `docs/PLAN.md`.
Read it entirely before writing any code. It is the single source of truth.

---

## Build & Run

The container is managed by a `docker-compose.yml` in the project root.

```bash
# Rebuild and restart after code changes
docker compose up -d --build athenaeum

# View logs
docker logs -f athenaeum

# Stop
docker compose stop athenaeum

# Access the app
open http://localhost:8741
```

The app serves on port **8741**. Data persists in `./data/` (mounted as `/data` inside the container).

**After any code change, always rebuild and restart the container before testing manually:**

```bash
docker compose up -d --build athenaeum
```

---

## Development Workflow

- Edit code in the repo root, then rebuild with the command above
- `./data/settings.yaml` contains real API keys — never commit the `data/` directory
- `./data/athenaeum.db` is the SQLite database — inspect with `sqlite3 ./data/athenaeum.db`
- Logs are the primary debugging tool: `docker logs -f athenaeum`

### After Making Changes

**Claude is responsible for rebuilding the container after every code change.** Always run the rebuild before reporting a task as done or asking the user to test:

```bash
docker compose up -d --build athenaeum
```

### Running Tests

Tests only need to be run before pushing to GitHub. Run them inside the project virtualenv:

```bash
.venv/bin/python -m pytest tests/ -v
```

### Cache Busting

`static/index.html` has a `?v=N` query string on the script tag. After any change to
`static/app.js` or `static/style.css`, increment `N` by 1. The HTML response is served
with `Cache-Control: no-cache` so browsers always revalidate the HTML, then the `?v=N`
ensures the JS/CSS is re-fetched when it changes.

```html
<script src="/static/app.js?v=4"></script>
<link rel="stylesheet" href="/static/style.css?v=4">
```

Bump both to the same version number together.

---

## Versioning

Tags follow semver (`major.minor.patch`) with `-beta.N` pre-release suffixes while in beta:

- `v1.0.0-beta.N` — beta releases
- `v1.0.0` — stable release
- After stable: patch for bugfixes, minor for new features, major for breaking changes

---

## Git Commits

All commits must end with:

```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Commit messages should be concise and describe *why*, not just *what*.
Use present tense. Example: "Add WAL mode to prevent database locking under load"

**When to commit:** Wait for explicit confirmation from the user before running
`git commit`. Stage changes and summarise what will be committed, then wait for
the go-ahead.

**Never push to GitHub** without the user's explicit instruction. `git push` is
off-limits unless the user asks for it in that specific message.

---

## ABS API Usage

ABS runs locally on the same Docker network — treat it like a local database call, not a remote API.

- **Always fetch full items** via `GET /api/items/{id}` for sync. The list endpoint (`/api/libraries/{id}/items`) returns minified items that omit series IDs, author IDs, and ebookFile. Never rely on minified list data for anything that needs to be normalised.
- **Concurrency is fine** — use `asyncio.gather` with a semaphore (10–20 concurrent) when fetching many items. There is no rate limit concern.
- **Prefer IDs over name-matching** wherever ABS provides them. Series, authors, and narrators all have stable IDs in full item responses. Store these IDs in the `_links` tables (`abs_series_id`, `abs_author_id`) so we can do exact lookups rather than fuzzy name matching.

---

## Code Conventions

These are defined in `docs/PLAN.md` and must be followed precisely:

- **Services** are instantiated per-request (not singletons). Read current settings at call time.
- **Database** access goes through `get_db()` only — never open connections directly.
- **Settings** access goes through `get_settings()` / `save_settings()` only — never read the YAML directly.
- **Deduplication** for request creation always goes through `_create_request()` — never inline.
- **INSERT OR REPLACE** must never be used on `author_links` or `series_links` — use INSERT OR IGNORE + targeted UPDATE.
- All multi-table state updates must be wrapped in a transaction.
- Background task bodies must be wrapped in try/except — exceptions are logged, never silently swallowed.

---

## Schema Changes

Never use bare `CREATE TABLE IF NOT EXISTS`. All schema changes go through the migration system in `app/database.py` (PRAGMA user_version blocks). See `docs/PLAN.md` → Database section.

---

## Style Rules

- **No emojis** anywhere — not in docs, code comments, commit messages, or any project file.

---

## Progress Tracking

`docs/PROGRESS.md` tracks build progress against the phases in `PLAN.md`.

**Update it whenever:**
- A phase or sub-task is completed — check the box and add a completion date
- A phase is started — note it as in progress
- Post-phase polish or fixes are done — add them as a named block (as with "Mobile UI polish")

Keep entries concise. The git log has the detail; PROGRESS.md is the at-a-glance view.

---

## Attribution

This project is being developed with Claude Code (Claude Sonnet 4.6).
The development process — including the original spec, adversarial review, and review-driven amendments — is documented in `docs/`.
