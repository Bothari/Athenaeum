# Athenaeum — Build Progress

Tracks completion against the phases defined in `PLAN.md`.
Updated after each phase or significant milestone.

---

## Phase 1: Foundation [complete]
_Completed 2026-04-04_

- [x] `Dockerfile` + `requirements.txt` (ffmpeg, croniter, all deps)
- [x] `app/database.py` — migration system, all 10 schema tables, `get_db()`
- [x] `app/settings.py` — `get_settings()` / `save_settings()`, asyncio lock, atomic write
- [x] `app/main.py` — `/healthz`, `/api/status`, static files, SPA catch-all
- [x] `static/index.html` — nav shell, bottom nav for mobile
- [x] `static/style.css` — full design system (variables, cards, badges, buttons, tables, forms, grid)
- [x] `static/app.js` — router, `api()`, `toast()`, all icons, `renderTable`, `renderSearchResults`, `expandRequestForm`, `confirmAction`, home/search page, all route stubs

**Notes:**
- App runs on port 8741 (8743 was already taken by another service)
- Port mapped `8741:8741` in `docker-compose.yml`

---

## Mobile UI polish (post-Phase 1)
_Completed 2026-04-04_

- [x] Bottom nav bar with icons (Search · Library · Queue · Dashboard · Settings)
- [x] Library tap on mobile shows Books / Authors / Series popup
- [x] Downloads merged into Queue page as a tab (`/#/requests?tab=downloads`)
- [x] `font-size: 16px` on all inputs — prevents iOS zoom-on-focus
- [x] Nav bar `position: sticky` on mobile
- [x] Home page hides nav bar on mobile, shows large inline "Athenaeum" title above search

## Desktop UI polish (post-Phase 1)
_Completed 2026-04-06_

- [x] Library dropdown opens on hover (not click)
- [x] Library nav item navigates to Books on click
- [x] Library button highlights on all `/library/*` routes
- [x] "Search" added as explicit desktop nav item
- [x] Mobile bottom nav search button uses search icon (not home)
- [x] Base font size bumped to 16px site-wide
- [x] Series icon replaced with book-spines-on-shelf SVG
- [x] Dropdown hover dead-zone gap removed

---

## Phase 0: CI Setup
_Completed 2026-04-06_

- [x] `.github/workflows/test.yml`
- [x] `.github/workflows/docker.yml`
- [x] `requirements-dev.txt`
- [x] `tests/conftest.py`
- [x] `tests/test_database.py` (smoke test)

---

## Phase 2: Settings & ABS [complete]
_Completed 2026-04-06_

- [x] `app/services/audiobookshelf.py` — all 6 methods, normalised item shape
- [x] `app/routes/settings.py` — GET/PUT settings, 4 connection test endpoints
- [x] Settings page frontend — tabs, form groups, test buttons, save (was already built in Phase 1 shell)
- [x] `tests/test_services/test_audiobookshelf.py` — 14 tests (normalize, test_connection, check_library, get_item_by_id, list_all_items, scan_library)
- [x] `tests/test_routes/test_settings.py` — 17 tests (GET masking, PUT validation, sentinel handling, cron validation, 4 test endpoints)

---

## Phase 3: Library Sync [complete]
_Completed 2026-04-06_

- [x] `app/services/library_sync.py` — `sync_library()`, `_sync_item()`, `_link_to_hardcover()`, `_get_or_create_author()`, `_get_or_create_series()`, `_split_authors()`, `_upsert_task_state()`
- [x] `app/routes/books.py` — GET /api/books, GET /api/authors, GET /api/series (with pagination, filtering, sorting), GET /api/books/{id}, GET /api/authors/{id}/books, GET /api/series/{id}/books
- [x] `app/routes/sync.py` — POST /api/sync/library, POST /api/sync/cache-refresh (placeholder)
- [x] `app/main.py` — background task loops for library_sync, cache_refresh, auto_search (cron-driven, skip if blank)
- [x] Library pages frontend — Books list, Authors list, Series list (already built in Phase 1 shell, now wired to real API)
- [x] `tests/test_services/test_library_sync.py` — 17 tests (_split_authors, _get_or_create_author/series idempotency, sync creates/deduplicates, INSERT OR IGNORE validation, new format on resync)
- [x] `tests/test_routes/test_books.py` — 22 tests (list endpoints, pagination, filtering, sorting, 404s)

---

## Post-Phase-3 polish (v0.3.0)
_Completed 2026-04-08_

- [x] `app/routes/abs_proxy.py` — `/api/abs/cover/{abs_id}` cover proxy (24h cache); `/api/abs/library-settings` returns `cover_aspect_ratio`
- [x] `list_all_items` rewritten to fetch full items concurrently (20-way `asyncio.gather`) — fixes missing series IDs, author IDs, and ebook detection
- [x] ABS author IDs stored via structured `authors` list in full item response, not flat string splitting
- [x] `CLAUDE.md` — new "ABS API Usage" section: always fetch full items, spam concurrently, prefer IDs over name-matching
- [x] Book/author/series detail pages — view toggle (list/poster), pinned top-right on mobile; state persisted globally via `localStorage`
- [x] Series position sort uses `CAST(bs.position AS REAL)` for correct numerical ordering
- [x] Debug view cards on book detail, author detail, and series detail pages showing link IDs
- [x] Cover URLs rewritten to proxy route when `abs_id` present; square covers toggled from ABS library setting (`cover_aspect_ratio === 1`)
- [x] Formats badges pill-shaped; formats column fixed-width `white-space: nowrap` in books list table
- [x] Author detail sortable table (client-side, click-to-sort columns)

## Post-Phase-3 polish (v0.3.1)
_Completed 2026-04-08_

- [x] HC linking: `cache_refresh` task with three passes — book linking (primary), author catch-up, series catch-up — rate-limited at ~60 req/min with exponential backoff on 429
- [x] Fix series linking: read `featured_series` + `series_names` from HC Typesense docs (dead `book_series` field removed); fuzzy-match local series name to get HC series ID
- [x] Fix author linking: extract HC author IDs from `contributions` field in search result
- [x] Fix audiobook detection: use `audioFiles` instead of `tracks`/`numTracks` (the latter requires ABS probing and is absent on fresh discovery)
- [x] `cache_refresh` fires automatically after `library_sync` completes
- [x] Stale `running=1` task_state flags cleared on startup
- [x] Missing links UI panel — surfaces books/authors/series with no HC ID
- [x] Mobile task card layout — "Last" row below "Next", no desktop change
- [x] HC API structure and linking strategy documented in `PLAN.md`

## HC matching tuning (v0.3.2)
_Completed 2026-04-10_

- [x] `?unlinked=1` filter on `/api/books`, `/api/authors`, `/api/series` — "Unlinked only" checkbox on list pages
- [x] Try-link endpoints (`POST /api/sync/try-link/book|author|series/{id}`) — run match on demand, persist if found, return full candidate log
- [x] Try-link UI on book/author/series detail pages — shows candidate table with t/a scores colour-coded against thresholds
- [x] Title normalisation: strip HC subtitle after colon (e.g. "Dust: Book Three…" → "Dust"), take max of full vs stripped score
- [x] Title normalisation: `&` → `and` before comparison ("Angels & Demons" ↔ "Angels and Demons")
- [x] Author normalisation: `_author_score()` removes all periods and spaces before comparing, takes max of token_sort_ratio and plain ratio — fixes "V. E. Schwab" ↔ "V.E. Schwab"
- [x] Multi-author books: a_score is best match across all local authors × all HC contributors — fixes "A Memory of Light" (Jordan + Sanderson)
- [x] HC book/author conflict guard: `_set_hc_author_id()` checks for existing claim before UPDATE, logs warning and skips rather than crashing
- [x] Search result depth: `per_page` bumped from 5 → 15 — fixes books that rank 6th+ in Typesense (e.g. "The Thursday Murder Club")
- [x] Dashboard task cards: Run Now buttons + live polling of running state
- [x] Dashboard mobile: task cards full-width stacked
- [x] Confirmed: HC `_ilike` WHERE queries are blocked server-side — Typesense search is the only viable path

## HC matching polish (v0.3.3)
_Completed 2026-04-11_

- [x] Shared `setupHcCard()` helper replaces three separate inline HC card implementations (book/author/series detail pages)
- [x] HC link card: no "Change match" toggle — unlink first, options appear naturally; linked state shows "Linked to Hardcover {type} #{id}" with clickable icon
- [x] HC icon aspect ratio fixed (was forced square); bare anchor in candidate table (no button wrapper)
- [x] Series candidates: also fetch HC series for the first linked book in the local series (`_hc_series_for_book`) and merge/sort via_book first
- [x] Ghost HC series entries (`books_count: 0`) filtered from all series search results
- [x] Author and series slug storage fixed — catchup passes backfill slugs for already-linked entities by ID match
- [x] Debug view flag (`settings.general.debug_view`) gates score badges in candidate table
- [x] `cache_refresh`: 429s now retry up to 5 times (queue-based) instead of counting as immediate failures
- [x] `cache_refresh`: live progress written to `task_state.last_result` every ~4s (linked/failed/remaining per phase); dashboard task card shows it alongside spinner
- [x] Book search runs title-only (3 pages) + title+author (1 page) concurrently, deduplicated by HC ID — fixes books buried in title-only results (e.g. "Strangers" by Belle Burden)
- [x] Candidate tables sorted by score descending across all three entity types

---

## Phase 6: Detail Pages [partial]
_In progress — detail pages built, book_links and missing-books logic pending_

- [x] Book detail page — metadata, authors, series, formats (in-library), ABS/HC link IDs in debug view
- [x] Author detail page — books table (sortable), debug card with `abs_author_id` / `hardcover_author_id`
- [x] Series detail page — books list/poster view with position and formats
- [ ] `app/routes/book_links.py` — ABS/Hardcover link/unlink endpoints
- [ ] Series missing-books detection (async, compare owned positions to HC series total)
- [ ] `tests/test_routes/test_book_links.py`

---

## Phase 4: Search & Requests [complete]
_Completed 2026-04-11_

- [x] `app/services/book_search.py` — HC Typesense search, `normalize_hit()`, `search_books()`, `advanced_search_books()`
- [x] `GET /api/search/metadata?q=...` and `GET /api/search/advanced?title=...&author=...&series=...` — annotated with `in_library`, `book_id`, `library_formats`, `existing_requests`, local series UUIDs
- [x] `POST /api/books` — create book from HC result + attach requests; dedup by hardcover_id then title match
- [x] `app/routes/requests.py` — `POST`, `GET` (paginated, filterable), `GET /:id`, `DELETE /:id`, `POST /sync-library`, `GET /:id/downloads`, `POST /:id/search-indexers` (Phase 5 stub)
- [x] `_create_request()` shared helper — dedup-aware, blocks duplicate active requests and matching narrator in_library entries
- [x] Search page wired (quick + advanced, URL-persisted state, in-place request success) — frontend already built in Phase 1
- [x] Requests list page wired — frontend already built in Phase 1

---

## Phase 5: Downloads
_Not started_

- [ ] `app/routes/requests.py` — search-indexers, download, organize endpoints
- [ ] `app/routes/downloads.py`
- [ ] `app/main.py` — `download_monitor` background task
- [ ] Request detail page, Downloads page

---

## Phase 6: Detail Pages
_Not started_

- [ ] `GET /api/book/detail` endpoint
- [ ] Book detail page — metadata, ABS linking, request management
- [ ] Author detail page
- [ ] Series detail page — completion, missing books (async)
- [ ] `app/routes/book_links.py`
- [ ] `app/routes/sync.py`

---

## Future Work / Backlog

- **Author deduplication on HC conflict**: when two local authors match the same HC author ID (e.g. "James S. A. Corey" / "James S.A. Corey"), merge the duplicate into the winner — re-point all `book_authors` rows, delete the duplicate author and its `author_links` row. Currently the second match is skipped and the duplicate stays unlinked.

- **Multiple narrators per audiobook**: ABS handles multiple narrator editions by putting them in separate directories with distinct naming schemes. Athenaeum currently tracks only one narrator per request. Supporting multiple editions would require a separate request per narrator, or a richer request model. Deferred — not needed for typical single-narrator libraries.

---

## Phase 7: Polish
_Not started_

- [ ] Dashboard stats page
- [ ] Active download polling (5s)
- [ ] Library sync progress display
- [ ] Mobile/responsive CSS fixes

---

## Phase 8: Authentication
_Not started — **spec needs review before implementation** (see big note in PLAN.md → Authentication)_

- [ ] `python-jose[cryptography]` + `passlib[bcrypt]` in requirements
- [ ] `auth.session_secret` auto-generated on startup
- [ ] `app/auth.py` — `require_auth` dependency, JWT + cookie helpers
- [ ] `app/routes/auth.py` — login, logout, me, set-password, OIDC endpoints
- [ ] Wire `Depends(require_auth)` onto all routers
- [ ] Frontend: boot auth check, login page (form + OIDC), logout in Settings
- [ ] Settings → Auth tab
