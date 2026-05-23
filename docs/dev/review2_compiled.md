# Athenaeum PLAN.md — Compiled Adversarial Review (Round 2)

Three reviewers assessed the updated plan: a **UI Expert** (interaction design, states, buildability), an **End User** (day-to-day usability, discoverability), and a **Maintainer** (ops, observability, longevity). This is a secondary review — issues already raised and addressed in Round 1 are not re-raised.

Individual reports: [review2_ui_expert.md](review2_ui_expert.md) · [review2_end_user.md](review2_end_user.md) · [review2_maintainer.md](review2_maintainer.md)

---

## HIGH

> Issues that will cause incorrect behaviour, user confusion, or significant rework.

---

### ~~1. Dashboard (`/#/`) has zero content specified~~ ✓ RESOLVED
Home page is now the search page. Dashboard moved to `/#/dashboard` with specified content (library totals + request pipeline counts). `GET /api/status` extended to include books/authors/series totals.

---

### ~~2. No empty states defined for any list page~~ ✓ RESOLVED
Per-page contextual empty states with action links added to plan. Books → sync or search. Authors/Series → sync. Requests → search. Downloads → calm "nothing downloading" with no action.

---

### ~~3. No first-run onboarding~~ ✓ RESOLVED
Non-dismissible yellow banner below nav when `audiobookshelf.url` is empty, linking to Settings. Disappears once ABS URL is saved.

---

### ~~4. No health endpoint — Docker healthcheck is unconfigurable~~ ✓ RESOLVED
`GET /healthz` added — runs `SELECT 1`, returns 200 `{ ok: true }` or 503 on DB failure. `HEALTHCHECK` added to Dockerfile and `docker-compose.yml`. `curl` added to apt-get install.

---

### ~~5. Sync/task status is in-memory — lost on restart~~ ✓ RESOLVED
`task_state` table added to schema. All three scheduled tasks upsert `running`, `last_run`, `last_result` on start/end. `GET /api/sync/status` reads from DB, persists across restarts.

---

### ~~6. Enrichment feature: routes are absent from the spec~~ ✓ RESOLVED
Enrichment superseded by inline HC auto-linking during library sync. Removed from Phase 7. No separate enrichment routes needed.

---

### ~~7. Failed requests are hard to find~~ ✓ RESOLVED
`/#/requests` list page added — filterable table with status/type dropdowns. Dashboard `failed` count card links to `/#/requests?requests_status=failed`. Row-level retry and delete actions.

---

### ~~8. `Requests` page columns are never specified~~ ✓ RESOLVED (with #7)
Columns specified: Book title, Author, Type (icon), Status (badge), Narrator (if set), Created date. This will almost certainly be wrong on the first build pass.

---

## MEDIUM

> Gaps that will cause confusion or require rework.

---

### ~~9. Book detail ABS linking section is entirely unspecified~~ ✓ RESOLVED
Three-state spec added: linked (show item + unlink button), unlinked with auto-search results (candidate rows + link button), unlinked no matches (manual search input).

---

### ~~10. `expandRequestForm` narrator input is unspecified~~ ✓ RESOLVED
Narrator input appears below format buttons only when audiobook is selected. Optional (null narrator is valid). Format buttons remain enabled when narrator differs from what's in library, showing "have (Narrator Name)". The deduplication logic is right but the UI for entering it is a blank.

---

### ~~11. No loading or error states for data-fetching pages~~ ✓ RESOLVED
Standard pattern defined: `renderLoading(container)` before fetch, `renderError(container, retryFn)` in catch. All route handlers follow this — no per-page spec needed.

---

### ~~12. Advanced search form state is not URL-persisted~~ ✓ RESOLVED
Search state persisted in URL hash params (`?q=...&author=...&advanced=1`). On render: pre-fill inputs and re-run search if `q` present. Clear button (✕) inside input clears all fields, params, and results. If the table approach is used for URL state, the search form should follow the same pattern.

---

### ~~13. No bulk operations on requests~~ DEFERRED
Added to Future Work section in plan. Per-row actions sufficient for initial build; `?status=failed` filter + Retry covers the most painful case.

---

### ~~14. Cron expression fields have no validation~~ ✓ RESOLVED
`PUT /api/settings` validates `schedule.*` values via `croniter(value, datetime.now())`, returning 400 with a field-specific error message on failure.

---

### ~~15. `metadata_cache` expired entries are never deleted~~ ✓ RESOLVED
`cache_refresh_task` purges entries where `expires_at < now() - 7 days` at the start of each run. Entries kept for 7 days after expiry (21 days total) before deletion.

---

## LOW

- ~~**No back-navigation pattern described**~~ — rely on browser back button. (UI Expert)
- **`library_formats` "have (Narrator A)" display format unspecified** — mentioned in prose but neither string format nor visual treatment is shown. (UI Expert)
- ~~**No 404 / unmatched-route handling**~~ ✓ RESOLVED — fallback route renders "Page not found." for unmatched hash paths. (UI Expert)
- ~~**Series missing-books: `truncated` not surfaced**~~ ✓ RESOLVED — note shown below missing list when `truncated: true`. Progress indicator not actionable (single API response). (End User)
- ~~**Sync status has no UI surface**~~ ✓ RESOLVED — Dashboard shows task state row (last run, last result, running indicator). Settings gains a Sync tab with cron inputs, manual trigger buttons, and inline status. (End User)
- ~~**No database backup guidance**~~ ✓ RESOLVED — backup note added to deployment section. (Maintainer)
- **Output volume path is a placeholder** — `docker-compose.yml` shows `/path/to/output:/output`; a user who copies this verbatim silently gets a broken organise path. (Maintainer)
- ~~**`merge_jobs` accumulates for in-library books**~~ ✓ RESOLVED — `merge_jobs` row deleted in `_auto_organize` step 10 when request reaches `in_library`. (Maintainer)

---

## Top Fixes Before Building

| # | Fix | Reviewer |
|---|-----|----------|
| 1 | Specify dashboard content (use GET /api/status counts + any quick links) | UI Expert, End User |
| 2 | Describe empty states for list pages | UI Expert |
| 3 | Add a settings-required banner or onboarding hint for first run | End User |
| 4 | Add `GET /healthz` endpoint + Docker HEALTHCHECK | Maintainer |
| 5 | Persist sync last_run/last_result to DB | Maintainer |
| 6 | Resolve enrichment: specify routes or delete Phase 7 item | Maintainer |
| 7 | Specify Requests page table columns | End User |
| 8 | Describe narrator input in expandRequestForm | UI Expert |
| 9 | Add cron expression validation to PUT /api/settings | Maintainer |
