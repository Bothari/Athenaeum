# Implementer Review — Athenaeum PLAN.md

## Persona
I am the person who has to actually write every line of code in this plan. My job is to find every place the plan will cause me to stop, guess, re-read three sections, contradict myself, or throw away work and redo it.

---

## Findings

### CRITICAL

- **`POST /api/books` does double duty as book-creation AND request-creation, but the state machine for skipping existing requests is never defined**: The endpoint body includes `requests: [{type, narrator?}]` and the response includes `_created_requests` and `_skipped_requests` counts, but the plan never defines *what makes a request "skipped"*. Is it skipped because the book already exists? Because a request for that format already exists? Because an `in_library` request already exists? Because a hard-deleted row existed and so the duplicate check says "no record, allowed"? The hard-delete policy makes this especially dangerous: after a user deletes a request, the duplicate check will see nothing and allow re-requesting, but the plan never says whether that is the *intended* behaviour at this endpoint or should be blocked by something else. An implementer will make a choice here, it will be wrong, and the frontend will show stale counts.

- **Background task lifecycle is undefined — `asyncio.create_task` in startup will silently die on any unhandled exception**: The plan specifies `asyncio.create_task(download_monitor())` etc., but gives no error handling strategy for these infinite loops. If `download_monitor()` raises any unhandled exception (e.g., database locked, network timeout to qBittorrent), the task is cancelled and never restarted. There is no mention of try/except, no mention of a supervision loop, no mention of logging the exception. The downloads page will appear to work (returns 200) but nothing will ever progress. This is a day-one production bug that will be very hard to diagnose.

- **`_auto_organize` is described as a "background task" but is triggered from within `download_monitor()`**: When `download_monitor()` calls `_auto_organize(request_id, download_path)`, does it `await` it (blocking the monitor loop for the full organize duration including the ABS poll retries of up to 50 seconds), or does it `asyncio.create_task()` it (meaning multiple organizes can run concurrently with no concurrency guard)? The plan does not specify. If awaited: the monitor misses all other downloads for up to 50 seconds per completion. If detached as a task: two organizes for the same file can race. This is architecturally unresolved.

- **`metadata_links.abs_id` has a `UNIQUE` constraint but ABS can have multiple libraries, and an item can appear in more than one ABS library**: `abs_id UNIQUE` means an internal book can only be linked to *one* ABS item. But the plan also says an ABS item can have *both* audiobook and ebook formats — and in `_auto_organize` step 7 it upserts `metadata_links` to set `abs_id`. If an ebook and an audiobook end up as separate ABS items (different IDs) but the same internal `book_id`, the second upsert will fail the `UNIQUE(book_id)` constraint on the `metadata_links` table. This is a concrete schema conflict.

- **`GET /api/downloads` says it returns "live progress from download client" but there is no spec for what happens when the download client is unreachable**: The Downloads page polls every 5 seconds. If qBittorrent is down, does the endpoint return cached DB status? Return a 503? Return an empty list? Return progress as `null`? The frontend calls `api(path)` which throws on non-2xx. A transient qBittorrent outage will break the entire downloads page with an uncaught exception and show nothing. No fallback is specified.

- **The `ingested_files` table has denormalised `author TEXT` and `title TEXT` columns despite the plan explicitly forbidding denormalised strings in the `books` table**: This contradiction means the organiser logic writes to a separate flat-string world while the rest of the app lives in a normalised JOIN world. The organiser then has to map back to the books schema to update `metadata_links`. The plan never explains how `ingested_files.author` (a plain string) maps back to the `authors` table or how conflicts are resolved. An implementer will either ignore `ingested_files` entirely or build a parallel string-based pipeline that never properly connects to the normalised schema.

---

### HIGH

- **`POST /api/books` vs `POST /api/requests` — two endpoints create requests, but the deduplication contract between them is never specified**: The `expandRequestForm` logic says "POST /api/books (creates book + requests), then POST /api/requests if book already existed." This means the frontend will sometimes call `/api/books` (which creates requests internally) and sometimes call `/api/requests` directly. The duplicate-prevention logic must therefore be duplicated in both endpoints, or centralised in a service layer — but the plan specifies neither.

- **`GET /api/settings` masks sensitive keys, but `PUT /api/settings` body is `{ settings: { key: value } }` with no schema**: The settings YAML has a nested structure (`prowlarr.api_key`, `general.output_dir`, etc.) but the PUT body is a flat `{ key: value }` dict. How are nested keys represented — as `"prowlarr.api_key"` dotted strings? As nested objects? As `{ prowlarr: { api_key: "..." } }`? The plan never says. The frontend Settings page will be built one way and the backend will parse it another way, and the mismatch will only appear at test time.

- **`DELETE /api/requests/{id}` deletes the row, but the state machine shows `Any state → cancelled (except in_library)`**: The state machine diagram explicitly shows a `cancelled` state transition. The "Request Deletion" section then explicitly says "Always DELETE the row. Never set status to 'cancelled'. Cancelled status was a historical mistake." These two sections directly contradict each other. A new implementer reading top-to-bottom will implement the `cancelled` transition (it is in the state machine), then re-read and rip it out.

- **The `author_links` table uses `author_id TEXT UNIQUE` which means one author can only have ONE entry in `author_links`**: If the sync finds an ABS author that was already linked to a Hardcover author, updating that author's `abs_author_id` requires an UPDATE, not an INSERT. SQLite's `INSERT OR REPLACE` on a table with two UNIQUE constraints (`author_id` and `hardcover_author_id`) will delete and re-insert, losing the other linked ID. This is a non-trivial upsert problem that the plan waves past.

- **`GET /api/series/{series_id}/missing` makes N+1 Hardcover API calls**: For a series with 20 books, this is 21 sequential Hardcover API calls. Hardcover's rate limits are not mentioned anywhere in the plan. The plan explicitly says "the workaround is correct — don't try to simplify it" which means the implementer must implement it exactly as described, including handling all the failure modes that are not described.

- **`renderTable(config)` is specified to have "sortable columns and text filter" but no implementation detail is given**: The sort state has to live somewhere (component-local variable? URL hash param?), the filter has to debounce, and it has to re-render without a full page reload. None of this is described. An implementer will invent their own approach, which may be inconsistent with the hash-router pattern, and the filter state will be lost on navigation and return.

- **`confirmAction(btn, confirmText, action)` inline confirmation is described but the DOM lifecycle is not**: If the user clicks the delete button in a request dropdown, it enters "confirm" state. If the user then navigates away and back (SPA re-renders `#app.innerHTML`), the confirmation state is blown away. If the user clicks a second delete button while the first is in confirm state, both are in confirm state simultaneously.

- **The enrichment background task (`POST /api/enrichment/start`) has no persistence**: `GET /api/enrichment/status` returns `{ running, processed, total, current_book }` — this state lives in memory. If the server restarts mid-enrichment (e.g., docker restart), the enrichment is silently abandoned and `GET /api/enrichment/status` will return `running: false` with zero progress.

- **Dockerfile and requirements.txt are listed as Phase 1 item 1, but their contents are never specified**: Missing: `uvicorn` (without it the app cannot run), `python-multipart` (FastAPI requires it for form data), any ASGI server configuration. The Dockerfile is never described — base image, working directory, copy steps, CMD — none of it.

---

### MEDIUM

- **`library_sync_task()` runs on startup with a 30-second delay, but the plan gives no guidance on what happens if ABS is unreachable at startup**: On first boot, the sync will fail. The plan does not say whether to log and continue, whether to retry, or how long to wait. The background task will die, and the library will never sync until the server restarts.

- **Cache buster on `index.html` is manual (`?v=N` on the script tag) but the plan never says when or by how much to bump it**: In Docker Compose without proper `Cache-Control` headers, the browser may cache the HTML file itself, making the `?v=N` on the script tag irrelevant. There is no mention of setting `Cache-Control: no-cache` on the HTML response. The plan identifies the problem but does not actually solve it.

- **`book_search.py` normalised result has `series` (string), `series_id` (string), and `all_series` (list) but the API search result shape only has flat `series: "..."` and `series_position: "7"`**: When a book belongs to multiple series, the API collapses it to a single `series` string. The plan never says how to pick which series to surface when there are multiple, or what the frontend does with `all_series` vs `series`.

- **`GET /api/book/detail?book_id=...&abs_id=...` is not in the Phase 4 or Phase 6 build order**: The endpoint appears in the books route spec but is never assigned to a phase. An implementer following the build order will skip it until they notice it missing during frontend work.

- **`PATCH /api/requests/{id}` says "Status transitions validated" but never says which transitions are legal**: The state machine diagram shows the flow but an implementer needs to know: is `downloading → requested` valid? Can a `completed` request go back to `monitored`? The `monitored → requested` back-transition is shown in the diagram but its use case is never explained.

- **`POST /api/requests/{id}/organize` says "manually trigger organize (e.g., if auto-organize failed)" but `_auto_organize` reads `download_path` from the download record**: If auto-organize failed because the file was moved or the path is wrong, the manual trigger will fail for the same reason. The endpoint gives no way to supply a corrected path.

- **`GET /api/abs/search?title=...&author=...` is under `metadata_links.py` in the spec but would more logically belong in `books.py`**: An implementer building `metadata_links.py` will have to import and instantiate the ABS service there. The plan never says where service instances are created — are they module-level singletons? Instantiated per-request? Dependency-injected via FastAPI `Depends()`?

- **`metadata_cache` table is defined in the schema but never referenced again**: There is no code that reads from or writes to `metadata_cache`. No spec for what queries get cached, what the TTL is, or how cache keys are constructed.

- **The `formats` field in the book detail shape is not backed by any table**: There is no `formats` table in the schema. The `formats` array shown in book detail must be derived from requests with `status='in_library'`, but the plan says elsewhere not to use request status to infer library presence. The plan never resolves where `book.formats` actually comes from in the API response.

- **`advanced_search` supports "grouping by series" using `settings.group_series_in_search`**: What does "grouping" mean in a flat JSON results array? Does it return one result per series with nested books? Does it deduplicate books that appear in a series? None of this is specified.

---

### LOW

- **`author_links.abs_author_id TEXT UNIQUE` will throw an IntegrityError instead of gracefully merging authors when ABS has a single author record that maps to two internal author records created from different title-string splits.**

- **The `position` field in `book_series` is `TEXT` to support values like `'4.5'` and `'Novella 1'`**: The sort step says `float(position)` — which will throw a `ValueError` on `'Novella 1'`. An implementer might write a bare `sorted(results, key=lambda x: float(x['position']))` and have it crash on the first non-numeric series position.

- **`_split_authors` splits on ` and ` (with spaces) but the filter is case-sensitive**: `"Mel Brooks AND Carl Reiner"` (uppercase AND) will not be split.

- **The nav item order is "logo | Search | Library ▾ | Requests | Downloads | Settings" but the route list shows `/#/` as the Dashboard with no corresponding nav item**: Users cannot navigate back to the dashboard except by clicking the logo (which is not specified) or manually editing the URL.

- **The single-file frontend (`static/app.js`) will grow to thousands of lines with no module system**: The plan explicitly accepts this tradeoff but gives no guidance on naming conventions, function ordering, or how to avoid global scope pollution. An implementer will drift toward inconsistent patterns by Phase 5.

- **Pushover notification settings are in `settings.yaml` but no notification endpoints, service file, or trigger points are mentioned anywhere in the plan**: Pushover is configured but never used. An implementer will either wire it up without guidance or ignore it entirely.

- **`GET /api/status` returns request counts by status but `cancelled` status no longer exists**: The status count object will need to be defined — the plan shows `{ requested: int, monitored: int, ... }` without listing all keys. If `cancelled` is removed from the state machine but not from the status count shape, the dashboard will show a zero entry that means nothing.

---

## Summary

The plan is substantially more complete than most project specs of this kind — the schema, the service contracts, and the "lessons learned" section are genuinely useful. The normalised schema decision is correct and the explanation of the BookOrganizeClaude failure modes is the kind of institutional knowledge that prevents repeat mistakes.

However, the plan has a structural problem: it defines *what* endpoints and tables exist without defining *how* they behave at the boundaries. The critical failure modes are all at the seams — between the state machine and the delete policy (direct contradiction), between the `books.POST` and `requests.POST` endpoints (duplicate deduplication logic with no shared contract), between the background tasks and their error handling (no supervision means silent death), and between the normalised schema and the `ingested_files` denormalised table (two different data models for the same entity). These seams are exactly where an implementer will spend most of their time, and the plan gives them the least guidance there.

The build order in Phases 1–7 is mostly sound, but Phase 4 mixes route completion with search service implementation and frontend work in a way that creates many in-progress surfaces simultaneously. The missing `GET /api/book/detail` endpoint is not assigned to any phase, and the enrichment routes (Phase 6) depend on background task infrastructure that is described in Phase 5's `main.py` step — meaning Phase 6 cannot actually be built standalone. The frontend single-file architecture will become a maintenance problem by Phase 5, and the plan does not provide enough structural guidance (naming, ordering, scope conventions) to keep a 3000-line vanilla JS file coherent across a multi-phase build.
