# Athenaeum v2 — Frontend Overhaul Plan

Rewrite the entire UI in Svelte 5 / SvelteKit. **Backend logic stays intact**: the
FastAPI app, its 62 JSON endpoints, the services layer, and the SQLite schema are
not in scope. This is a frontend replacement against a stable API.

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
│   │   └── app.css
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
2. **Shell** — layout, nav, routing, auth guard, API client, toast. Login and
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
   - **5b — TODO.** The per-format interaction surface:
     `renderDetailFormatContent` (indexer search, download, request state
     changes) and `renderProwlarrResults`. Shared with `/requests`, so worth
     doing alongside phase 6.

6.5. **Home / search** — MISSING FROM THE ORIGINAL PLAN. The `/` route (160
   lines) plus the request card it shares with author detail's "Also by" section
   (`populateBookCard` 75 + `buildFormatRows` 131). Must be scheduled; author
   detail is incomplete until it exists.
6. **Requests** (459 LOC) — first genuinely complex one.
7. **Series detail** (879 LOC) — pack search and download flows.
8. **Settings** (1,151 LOC) — tab by tab; leave for last, it is mostly forms and the
   most mechanical.
9. **Cutover** — Dockerfile build stage, delete `static/app.js` + `style.css`,
   point prod at the new build.

Phases 1–3 are the ones worth getting right slowly; 4–8 are largely mechanical once
the primitives exist.

## 9. Open decisions

- **Where does `frontend/` live?** Same repo as proposed here (simplest, one
  Dockerfile) versus a separate repo.
- **Test strategy.** Whether v2 UI gets component tests (vitest) or leans on the
  existing pytest suite for the API contract.
