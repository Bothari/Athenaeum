# Architect Review — Athenaeum PLAN.md

## Persona
I evaluate system design, database schema, API contracts, and structural decisions with a focus on correctness, evolvability, and long-term maintainability. I ask: will this design hold up after first deployment?

## Findings

### CRITICAL

- **No schema migration strategy**: `CREATE TABLE IF NOT EXISTS` provides no path to evolve the schema after first deployment. There is no `PRAGMA user_version` check, no migration runner, no versioning at all. This is precisely the pain BookOrganizeClaude suffered — it's just been deferred again to the first time a column needs adding.

- **`author_links` / `series_links` UNIQUE constraints on nullable external-ID columns**: `UNIQUE` on `hardcover_author_id` and `abs_author_id` means one external-ID row per author. Pen names, merged Hardcover records, or an author appearing in both ABS and Hardcover under different IDs are all unrepresentable without a migration. The junction-table pattern (one row per external-ID) would be more correct.

- **`metadata_links.abs_id TEXT UNIQUE` is too tight for multi-library setups**: Settings explicitly support `library_id: "id1,id2"` (comma-separated multiple libraries). A book appearing in two libraries under different ABS item IDs will fail to link — the UNIQUE constraint blocks a second row for the same `book_id` with a different `abs_id`. The schema cannot represent multi-library duplicates.

- **`_auto_organize` has no failure recovery path**: A crash or exception mid-organize leaves the request stuck in `organizing` with no error visible to the user and no described transition back out. The state machine diagram shows `organizing → completed | failed` but the implementation notes describe no mechanism to reach `failed` from `organizing`, and there is no retry or manual-reset endpoint.

### HIGH

- **Dual status updates not wrapped in a transaction**: `download_monitor` updates both `downloads.status` and `requests.status` as separate writes. A crash between the two leaves permanently inconsistent state. SQLite supports transactions — they must be used here.

- **`DELETE /api/requests/{id}` orphans child rows**: `downloads` and `ingested_files` reference `requests(id)` via FOREIGN KEY, but SQLite foreign key enforcement is OFF by default (`PRAGMA foreign_keys = OFF`). No `ON DELETE CASCADE` is specified. Hard-deleting a request leaves orphaned download and ingested_file rows silently.

- **`POST /api/books` conflates book creation and request creation**: The endpoint creates a book AND its initial requests in one shot, and the plan relies on this for the primary add-book flow. This couples two concerns, duplicates logic that `POST /api/requests` also must handle, and makes the response shape with `_created_requests` / `_skipped_requests` an invisible side-effect rather than an explicit operation.

- **`GET /api/series/{id}/missing` makes N+1 Hardcover API calls**: The algorithm calls `search(title)` for every book in the series sequentially, with no batching, rate limiting, or described timeout. A series with 20 books makes 21 sequential outbound HTTP calls in a single request handler.

- **Background tasks share no mutex**: `download_monitor` (runs every 15s) and a user-triggered `POST /api/requests/{id}/organize` can race on the same request simultaneously. No locking, advisory or otherwise, is described.

- **`library_sync` has no update path**: The sync logic checks `metadata_links.abs_id` and skips if found. This means metadata changes in ABS (title corrections, narrator updates, new formats added) are silently ignored after first sync. There is no described mechanism to re-sync or refresh an existing item.

### MEDIUM

- **`metadata_cache` has no eviction policy**: The table accumulates search results indefinitely. No TTL, no max-rows, no described cleanup. For an active installation this will grow without bound and stale results will never expire.

- **Settings have no type validation**: `PUT /api/settings` is described as validating "paths exist" but performs no type checking. An integer written where a string is expected, or a negative interval, will propagate silently until runtime failure.

- **`ingested_files` is a denormalised island inside a normalised schema**: The table has `extracted_title`, `extracted_author`, `title`, `author`, `narrator` as free-text columns — no FK to `books`, `authors`. This is inconsistent with the schema's stated design principle of "no denormalised strings."

- **`abs_checked_at` column on `books` is never written**: No described code path sets this field. It appears to be a leftover from a previous design iteration with no described purpose or writer in the current plan.

- **State machine transition matrix is underspecified**: The diagram shows `Any state → cancelled (except in_library)` but the plan elsewhere says "always hard-delete, never set cancelled." These two statements directly contradict each other. The cancelled status should be removed from the diagram entirely if it is not used.

- **`search-indexers` endpoint blocks with no timeout policy**: `POST /api/requests/{id}/search-indexers` makes outbound Prowlarr calls synchronously in the request handler. No timeout is specified. A slow or unresponsive Prowlarr instance will hold an HTTP connection open indefinitely.

### LOW

- **TEXT UUIDs vs INTEGER rowids**: Using `TEXT PRIMARY KEY` for every table forces SQLite to use the text as the B-tree key. `INTEGER PRIMARY KEY` is an alias for `rowid` and is significantly faster for range scans. For a personal-use app this is unlikely to matter in practice, but it's an unnecessary pessimisation.

- **`float(position)` sorting will raise on non-numeric positions**: The plan says sort by `float(position)` and "put non-numeric last." Converting `"Novella 1"` or `"0.5a"` with `float()` raises `ValueError`. The plan acknowledges this but provides no implementation guidance for the exception handler.

- **Manual cache-busting (`?v=N` on script tag) is fragile**: The plan itself lists this as a historical failure point. The proposed solution is identical to what failed before — still requiring a manual bump. A content hash or build timestamp would be more reliable.

- **No authentication acknowledgement**: The plan makes no mention of auth, assuming the app runs on a trusted network. This is a reasonable choice for a self-hosted tool, but the absence of even a note means an implementer may add token checks inconsistently or not at all.

- **Comma-separated `library_id` string instead of a YAML list**: `library_id: "id1,id2"` requires custom parsing logic. YAML natively supports lists (`library_ids: [id1, id2]`); using a comma-separated string is an unnecessary footgun.

## Summary

The schema design is largely sound — normalising authors and series into junction tables is the right call and avoids the exact problems that plagued BookOrganizeClaude. The state machine is conceptually correct. The service layer decomposition is clean.

However, the plan has two structural gaps that will cause real pain: the absence of any schema migration strategy, and the lack of SQLite transaction discipline around multi-table state updates. Both are solvable before implementation begins with minimal effort (a `user_version` check function and a habit of wrapping related writes in `async with db.execute("BEGIN")`), but neither is described.

The N+1 Hardcover call in the missing-books algorithm and the orphaned-rows problem on request deletion are the next highest priority fixes. Everything else is refinement.
