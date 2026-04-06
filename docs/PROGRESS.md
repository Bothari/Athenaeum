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

---

## Phase 0: CI Setup
_Not started_

- [ ] `.github/workflows/test.yml`
- [ ] `.github/workflows/docker.yml`
- [ ] `requirements-dev.txt`
- [ ] `tests/conftest.py`
- [ ] `tests/test_database.py` (smoke test)

---

## Phase 2: Settings & ABS
_Not started_

- [ ] `app/services/audiobookshelf.py`
- [ ] `app/routes/settings.py` — GET/PUT settings, 4 connection test endpoints
- [ ] Settings page frontend — tabs, form groups, test buttons, save

---

## Phase 3: Library Sync
_Not started_

- [ ] `app/services/library_sync.py`
- [ ] `app/routes/books.py` (partial) — GET /api/books, GET /api/authors, GET /api/series
- [ ] Library pages: Books list, Authors list, Series list

---

## Phase 4: Search & Requests
_Not started_

- [ ] `app/services/book_search.py`
- [ ] `app/routes/books.py` (complete) — search, series missing, book detail
- [ ] Search page (quick + advanced, in-place request success)
- [ ] `app/routes/requests.py` — CRUD, sync-library
- [ ] Requests list page, request UI on book cards/detail

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
