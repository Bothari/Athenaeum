# Athenaeum v2 — Frontend Overhaul Plan

Rewrite the entire UI in Svelte 5 / SvelteKit. **Backend logic stays intact**: the
FastAPI app, its 62 JSON endpoints, the services layer, and the SQLite schema are
not in scope. This is a frontend replacement against a stable API.

---

## Status — 2026-08-10

**The rewrite is complete. Only cutover (§8, item 9) remains.**

Everything is on the long-lived `dev` branch, in the worktree
`~/Projects/Athenaeum-dev`. 18 commits, working tree clean, nothing pushed.
Production has not been touched at any point.

| | |
|---|---|
| Routes ported | all 14, plus home/search; no stubs remain |
| Backend fixes | done (§8, item 8c) — user deletion, prowlarr tags, dead keys |
| Checks | `svelte-check` 0/0, `npm run check:zoom` passes, 205 pytest tests pass |
| Not done | cutover: Dockerfile build stage, delete v1 assets, merge to `main`, tag, rebuild prod |

**Where things run**

| | |
|---|---|
| `athenaeum` (8741) | production, real DB, still serving v1 from `main` |
| `athenaeum-dev` (8742) | dev backend, **cloned** DB and settings, serves v1's assets |
| `athenaeum-dev-ui` (5173) | Vite dev server — this is where v2 is, LAN only |

v2 is reachable at `http://10.0.0.50:5173`, not on any public hostname.

**Carried over into cutover**

- Apply the dead-key cleanup to production's `settings.yaml` **after** deploying,
  never before — `main` still reads the singular `prowlarr.tag`, so removing it
  early silently disables tag filtering. Detail in `V2_SETTINGS_INVENTORY.md`.
- The `athenaeum-dev` and `athenaeum-dev-ui` service definitions live in
  `/mnt/config/htpc/docker-compose.yml`, which is not version-controlled.
  Cutover also edits the production service there.
- Merge `main` back into `dev` after the release so the branches do not drift.

**Worth knowing for whoever picks this up:** every UI bug found during this work
was found by using the app, not by a check — ragged table rows, filters that did
nothing on a hard load, square covers, a settings tab that failed to render. All
of them passed typechecking and the build. Mobile especially needs a real device.

---

## 1. Why

The current UI is a single 4,506-line `static/app.js`, plus 1,213 lines of CSS and a
65-line `index.html`. No build step. Concretely:

| Signal | Count | Meaning |
|---|---:|---|
| `innerHTML` assignments | 158 | UI built by string concatenation |
| `addEventListener` calls | 64 | Hand-wired, manually torn down |
| Top-level functions | 51 | No module boundaries |
| Routes in a hand-rolled hash router | 14 | Regex pattern matching, `location.hash` |

State lives in module-level `let` bindings (`_authUser`, `_routes`, `_prevPath`) with
`sessionStorage` used ad hoc for things like scroll restoration. Every route handler
re-renders its whole subtree by assigning `innerHTML`, so there is no diffing and no
component reuse — `renderBookCard`, `renderAuthorCard`, `renderSeriesCard`, and
`renderTable` are four separate hand-rolled templating systems.

This is exactly the code a component framework deletes. The rewrite is justified on
maintenance grounds alone, independent of any feature goals.

## 2. Stack decision

**SvelteKit 2 + Svelte 5 (runes) + `adapter-static` in SPA mode + TypeScript +
scoped component styles.**

Decided: v2 is a **faithful visual port** of v1 — same look, rebuilt. Redesign is a
separate exercise made cheap by having real components. Styling uses Svelte's scoped
`<style>` blocks with the existing `style.css` lifted into CSS custom properties, so
1,213 lines of working CSS are preserved rather than retyped. No Tailwind.

Each piece, on its own merits:

**SvelteKit over plain Svelte + Vite.** You get file-based routing, layouts, and
route groups instead of hand-rolling a router again — which is precisely what v1 did
and precisely what hurt. The cost is a heavier toolchain that mostly exists to serve
SSR you won't use.

**`adapter-static` with `ssr = false`, not `adapter-node`.** The FastAPI backend
already owns auth, sessions, OIDC, and the entire data layer. A Node server would mean
a second container, a second auth surface, and proxying every request. With
`adapter-static`, Vite compiles to plain assets that drop into `static/` and FastAPI
serves them as it does today. One container, one auth surface, deployment unchanged.

**TypeScript.** The strongest independent argument here: 62 backend endpoints with
non-trivial response shapes, and v1 has zero of that documented anywhere except by
reading route handlers. Types make the API surface legible and catch drift when the
backend changes. This is worth the cost even if nothing else were changing.

**Clean URLs work with no backend change.** `app/main.py:328` already has a catch-all
`serve_spa` returning `index.html`, so `/library/series/42` resolves correctly on hard
refresh. The `#/` hash routing goes away.

## 3. Target layout

```
Athenaeum/
├── app/                     # unchanged — FastAPI
├── frontend/                # new — SvelteKit source
│   ├── src/
│   │   ├── routes/
│   │   │   ├── (auth)/      # login, change-password
│   │   │   └── (app)/       # everything behind a session
│   │   ├── lib/
│   │   │   ├── api/         # typed client, one module per backend router
│   │   │   ├── components/  # shared primitives
│   │   │   ├── stores/      # auth, toasts (runes-based)
│   │   │   └── types/       # API response types
│   │   ├── app.css          # tokens, reset, zoom guard
│   │   └── app.html         # viewport meta
│   ├── scripts/
│   │   └── check-zoom.mjs   # CI guard for the mobile zoom rule
│   ├── vite.config.ts       # adapter + compiler opts + /api proxy
│   └── package.json
├── static/                  # build output (gitignored after cutover)
└── Dockerfile               # + node build stage
```

## 4. Route map

Current handlers, sized. Three routes are 55% of the codebase and carry all the risk.

| Current (hash) | v2 path | LOC | Notes |
|---|---|---:|---|
| `/settings` | `/settings` | 1,151 | 8 tabs; the single biggest unit |
| `/library/series/:id` | `/library/series/[id]` | 879 | Series detail, pack search, downloads |
| `/requests` | `/requests` | 459 | Queue, admin approve/reject |
| `/dashboard` | `/dashboard` | 200 | Admin only |
| `/` | `/` | 160 | Home / search |
| `/library/book` | `/library/book/[id]` | 157 | Promote `book_id` query to a path param |
| `/library/authors/:id` | `/library/authors/[id]` | 144 | |
| `/login` | `/(auth)/login` | 78 | Form + OIDC handoff |
| `/library/books` | `/library/books` | 50 | |
| `/library/series` | `/library/series` | 44 | Scroll restoration state |
| `/change-password` | `/(auth)/change-password` | 43 | |
| `/library/authors` | `/library/authors` | 30 | |
| `/profile` | `/profile` | 24 | |
| `/downloads` | `/downloads` | 6 | Redirect shim |

Settings tabs to become sibling routes under `/settings`: General, ABS, Prowlarr,
Downloads, Hardcover, Notifications, Tasks, Auth.

## 5. Shared components to extract

The current code has these concepts tangled into route handlers. They become the
component library, built first:

- `DataTable` — replaces `renderTable` (sorting, headers, empty states)
- `BookCard`, `AuthorCard`, `SeriesCard` — replace three near-duplicate renderers
- `LoadingState`, `ErrorState`, `EmptyState` — replace `renderLoading` / `renderError`
- `Toast` — replaces the manual `toast()` + `setTimeout` removal
- `DetailStats` — replaces `renderDetailStats`
- `TryLinkLog` — replaces `renderTryLinkLog` (879-line series route depends on it)
- `Nav` — replaces `updateNavForRole` / `updateActiveNav` imperative DOM poking;
  role-based visibility becomes declarative

## 6. API + auth layer

Replace the single `api()` helper with typed modules mirroring the backend routers:
`books`, `requests`, `settings`, `sync`, `auth`, `downloads`, `abs_proxy`.

Auth behaviour to preserve exactly:
- Session cookie set by FastAPI; the frontend never handles tokens
- A `401` from any call redirects to login **preserving the destination** (current
  `next` param behaviour) and honours the `force_local` sessionStorage flag
- `force_password_change` on the user object gates into `/change-password`
- Role gating: `isAdmin()` currently defaults to **true when `_authUser` is null** —
  this is a latent bug worth fixing deliberately in v2, not porting as-is

OIDC needs no frontend change: `/api/auth/oidc/start` is a plain redirect.

## 7. Build and container changes

**Dockerfile** gains a build stage:

```dockerfile
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
...
COPY --from=frontend /frontend/build ./static
```

**Dev containers.** `athenaeum-dev` (port 8742) keeps running uvicorn `--reload` and
serves the v1 UI, so the working app stays available throughout the migration.
`athenaeum-dev-ui` runs `vite dev` on port 5173 against the same backend, proxying
`/api` to `athenaeum-dev`. Bound on all interfaces so phones on the LAN can reach it
at `http://10.0.0.50:5173` — mobile testing is mandatory given the zoom rule.

Host Node is 18 (EOL) and cannot run modern Vite or the Svelte MCP. All Node tooling
runs via `docker run --rm node:22-alpine`; `athenaeum-dev-ui` uses the same image as a
plain runtime over the bind-mounted worktree, so there is no image to rebuild.

The dev container already runs against a **cloned database**, so all of this can be
exercised against real data with no risk to production.

## 8. Sequencing

Each phase ends with something runnable at `athenaeum-dev.bothari.com`.

1. **Scaffold** — DONE (2026-08-08). SvelteKit + TS in `frontend/`, adapter-static SPA,
   Vite proxy, `athenaeum-dev-ui` container serving HMR on :5173, tokens ported,
   zoom guard in place and verified. Nothing migrated yet.

   Note: current SvelteKit has **no `svelte.config.js`** — the adapter and compiler
   options live in `vite.config.ts` under the `sveltekit()` plugin.
2. **Shell** — DONE (2026-08-08). Layout, nav, routing, auth guard, API client, toast. Login and
   change-password work end to end. This proves the auth model before anything else.
3. **Component library** — DONE (2026-08-08). The §5 primitives, minus `TryLinkLog`.

   `TryLinkLog` is deliberately deferred to phase 7, where its only consumer
   (series detail) is ported. It is ~200 lines shaped entirely by that page's
   needs, and building it blind risks designing the wrong props and rewriting it.
4. **Small routes** — DONE (2026-08-09). Profile, downloads, books/authors/series
   lists, dashboard.

   Not ported: the series list's scroll restoration, which in v1 stashed
   `{scrollY, count}` in sessionStorage and re-fetched pages until the count was
   reached. Revisit once the series detail route exists to navigate back from.
5. **Detail routes** — split, because the original sizing was wrong.

   §4's table sized routes by their handler length and ignored the shared helpers
   they call. Book detail is really ~712 lines of v1 (handler 157 +
   `renderDetailFormatContent` 225 + `setupHcCard` 155 + `renderDetailFormats` 75
   + `renderProwlarrResults` 56 + `renderTryLinkLog` 44), and author detail adds
   ~350. That is larger than `/settings`, which was scheduled last as the big one.
   Series detail in phase 7 is underestimated the same way.

   - **5a — DONE (2026-08-09).** Book detail (info card, format summary) and
     author detail (list/poster views, sorting), plus `HardcoverCard` and
     `TryLinkCandidates` — the `setupHcCard`/`renderTryLinkLog` port, shared by
     book, author and series detail. Moved forward from phase 7, where it was
     wrongly parked as having no consumer yet.
   - **5b — DONE (2026-08-09).** The per-format interaction surface:
     `renderDetailFormatContent` (indexer search, download, request state
     changes) and `renderProwlarrResults`. Shared with `/requests`, so worth
     doing alongside phase 6.

6.5. **Home / search** — DONE (2026-08-09). Was missing from the original plan.
   The `/` route plus `SearchCard` and `FormatPills` (`populateBookCard` +
   `buildFormatRows`), including the author/series id pivots.
6. **Requests** — DONE (2026-08-09). Queue page with requests, downloads, pending
   and search-all tabs, the manual request dialog and the two-stage confirm button.
7. **Series detail** — DONE (2026-08-09). Books list (list/poster with position
   badges), missing/upcoming sections with "add to this series", the series pack
   flow (search, download, mapping review, organise) and Hardcover linking.

   Came in cheaper than its 879 lines suggested, unlike phase 5: every helper it
   calls — DetailStats, HardcoverCard, SearchCard, BookCard, ProwlarrResults —
   already existed, so the route was almost entirely its own logic. Sizing by
   handler length is only misleading when the helpers are unported.
8. **Settings** — DONE (2026-08-10). A deliberate rewrite, not a line-by-line port. Field
   checklist and structure in `docs/V2_SETTINGS_INVENTORY.md`.

   - **8a — DONE (2026-08-09).** General, ABS, Prowlarr, Downloads, Hardcover,
     Notifications, Tasks.
   - **8b — DONE (2026-08-10).** Auth (523 LOC) as its own step: it carries user management —
     create, delete, role changes, password resets — which is the
     highest-consequence surface in the app and should not ride along with six
     form tabs.

8c. **Backend fixes** — DONE (2026-08-10), in three separate commits.
   Five stored keys are read by nothing (see the inventory §3). Two are actively
   misleading and should be fixed at the source rather than papered over in the
   UI:

   - `prowlarr.tags` (plural) is in `DEFAULT_SETTINGS` but the backend reads the
     singular `prowlarr.tag` (`app/services/download_clients.py:230`). Editing
     the wrong one silently does nothing.
   - `auto_search.enabled` is never read; `auto_search.py` uses `max_attempts`,
     `min_seeders` and `ranking` only. Auto-search is gated by
     `schedule.auto_search` instead.

   The other three are merely inert and can be dropped whenever convenient:
   `audiobookshelf.square_book_covers` (cover shape comes from the ABS library's
   own `coverAspectRatio`), `general.group_series_in_search`, and
   `pushover.app_token` / `pushover.user_key` (superseded by
   `notifications.urls`).

   None of these are regressions from the port — all pre-date it. v2 deliberately
   builds no UI for any of them.

   **Deleting a user with requests returns a 500.** Also pre-existing — v1 hit the
   same failure. `requests.requested_by_user_id` references `users(id)` with
   `ON DELETE NO ACTION`, so SQLite refuses the delete and the uncaught
   `IntegrityError` surfaces as a bare 500 from
   `app/routes/auth.py` → `delete_user`. Any user who has ever made a request is
   therefore undeletable; on the dev clone that is three of five accounts.

   Agreed fix: **orphan the requests**. Inside the same transaction, before the
   delete:

   ```sql
   UPDATE requests SET requested_by_user_id = NULL WHERE requested_by_user_id = ?
   ```

   Chosen over cascading the requests away because a request's value does not
   depend on who asked for it, and those requests may have produced books still
   in the library. No schema migration is needed — the column is already
   nullable, so this needs no `ON DELETE` change and no table rebuild (SQLite
   cannot alter a foreign key in place).

   Also wrap the delete so an `IntegrityError` returns a 4xx with a readable
   message rather than a 500. The bare 500 is what made a backend constraint look
   like a broken button.
9. **Cutover** — released as **v2.0.0**, i.e. a `dev` → `main` merge.

   Steps:
   1. Add a Node build stage to the Dockerfile that runs `vite build` and copies
      the output into `static/`.
   2. Delete `static/app.js` and `static/style.css` (~5,700 lines of v1) and the
      `/dev/components` gallery.
   3. Merge `dev` into `main`, tag per the versioning rules in CLAUDE.md.
   4. Rebuild prod, which builds from `main`.

   **Decisions made, so they are not reopened:**

   - **v1 is not kept runnable.** It is deleted at cutover and survives only in
     git history. No `/v1` route, no preserved assets.
   - **`dev` is a long-lived integration branch**, not merged-and-deleted.
     Releases are `dev` → `main` merges at major versions. The containers already
     track this: prod builds from `~/Projects/Athenaeum` on `main`,
     `athenaeum-dev` from the worktree `~/Projects/Athenaeum-dev` on `dev`.
     After a release, merge `main` back into `dev` so hotfixes committed straight
     to `main` do not cause drift.
   - **The Vite dev server stays indefinitely.** `athenaeum-dev-ui` is not retired
     at cutover — it is how UI iteration happens. Only production is Node-free,
     which is what `adapter-static` was chosen for.
   - **Not version-controlled:** the `athenaeum-dev` and `athenaeum-dev-ui`
     service definitions live in `/mnt/config/htpc/docker-compose.yml`, which is
     not a git repo. Cutover also edits the prod service there.

Phases 1–3 are the ones worth getting right slowly; 4–8 are largely mechanical once
the primitives exist.

## 10. Outstanding stubs

None. Both are closed:

- **"Also by this Author"** — done 2026-08-09. Author detail calls
  `GET /api/authors/{id}/also-by` and renders results with `SearchCard`,
  keeping v1's empty and failure wording.
- **Series list scroll restoration** — done 2026-08-09, and generalised: position
  is restored on the books, authors, series and requests lists plus the author
  and series pages. Paginated lists replay pages until the saved row count is
  reached before jumping. See `lib/scroll.ts`.

## 11. Open decisions

- **RESOLVED — where `frontend/` lives.** Same repo, one Dockerfile.
- **STILL OPEN — test strategy.** The frontend has no automated tests. It relies
  on `svelte-check`, `check:zoom` and manual testing; the backend keeps its
  pytest suite (205 tests). Every UI bug found so far was found by using the app,
  not by a check — the table row heights, the mobile-only filter failures, square
  covers, and the Downloads tab all passed typechecking and the build. Worth
  deciding whether component tests (vitest) earn their place.
- **STILL OPEN — release flavour.** Whether cutover ships as `v2.0.0` or
  `v2.0.0-beta.1` with a soak period on production first.
