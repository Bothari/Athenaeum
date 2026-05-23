# Skeptic Review — Athenaeum PLAN.md

## Persona
I am an adversarial reviewer who assumes production systems will fail at their weakest points, external services will misbehave, and underspecified behaviour will be implemented inconsistently. My job is to find every gap before it becomes a bug.

---

## Findings

### CRITICAL

- **No database migration strategy**: The plan mandates starting with the full normalised schema, but provides zero strategy for what happens when the schema needs to change in a running deployment. SQLite's ALTER TABLE is severely limited (no DROP COLUMN before SQLite 3.35, no RENAME COLUMN before 3.25). There is no mention of schema versioning, `PRAGMA user_version`, Alembic, or a hand-rolled migration runner. The first time a column needs to be added or a new table introduced after go-live, the developer will be doing dangerous `DROP TABLE / recreate` operations on a live database containing user data.

- **No concurrency control on SQLite writes**: The plan uses `aiosqlite` with three concurrent background tasks (`download_monitor`, `library_sync_task`, `auto_search_task`) plus live API request handlers — all writing to the same SQLite file simultaneously. SQLite in WAL mode can handle concurrent readers but only one writer at a time. The plan never mentions enabling WAL mode (`PRAGMA journal_mode=WAL`), setting a `busy_timeout`, or using a connection pool with write serialisation. Under any real load — e.g., a library sync running while a download monitor fires while a user saves settings — the application will throw `sqlite3.OperationalError: database is locked` errors that will silently swallow state transitions.

- **`_auto_organize` has no atomicity or rollback**: The file organisation step (move/rename files → scan ABS → poll ABS → update DB) is described as a sequence with no error handling between steps. If the process crashes after files are moved but before the DB is updated, the file is gone from its original location and the DB still shows the old state. There is no idempotency mechanism, no "did I already move this file?" check, no rollback path, and no way to re-run safely. The `organize` endpoint exists as a manual retry, but re-running after a partial move will try to move a file that no longer exists at the source path.

- **`DELETE /api/requests/{id}` with no cascade definition**: The plan says "ALWAYS DELETE the row" but the schema has a `downloads` table with `request_id TEXT NOT NULL REFERENCES requests(id)` and an `ingested_files` table with `request_id TEXT REFERENCES requests(id)`. SQLite foreign key enforcement is OFF by default (`PRAGMA foreign_keys = OFF`). If the implementation never enables it, deleting a request will leave orphaned rows in `downloads` and `ingested_files`. If it IS enabled without `ON DELETE CASCADE`, the delete will fail with a foreign key constraint error. The plan is silent on both `PRAGMA foreign_keys` and cascade behaviour.

- **Race condition in missing-books algorithm**: Step 2 of the missing-books algorithm does one Hardcover `search(title)` call per book in a series. For a 20-book series, that is 20 sequential (or concurrent) API calls made per page load. The plan never mentions rate limiting, backoff, or what happens when Hardcover's API returns a 429 or times out mid-series. The frontend "loads missing books async in background" but there is no cancel mechanism if the user navigates away — the background fetch continues consuming Hardcover API quota. For prolific series (Discworld: 41 books, Wheel of Time: 14 books), this is a guaranteed rate-limit hit.

### HIGH

- **`metadata_links.abs_id UNIQUE` constraint breaks multi-library setups**: ABS supports multiple libraries (the settings even allow `library_id` as comma-separated). The `metadata_links` table has `abs_id TEXT UNIQUE`. If a book appears in two ABS libraries with different item IDs, only one can be stored. The sync logic says "if abs_id exists, skip" — so the second library's item will never be linked. This silently drops data with no error.

- **`author_links` upsert logic is entirely unspecified**: The table has `UNIQUE` constraints on both `hardcover_author_id` and `abs_author_id`. If the app tries to create/update an author link for an author already linked to Hardcover but not yet to ABS, the upsert logic (never described) could clobber the existing Hardcover link. There is no specification of how these rows are created, updated, or merged.

- **ABS polling in `_auto_organize` has no concurrency guard**: "Poll ABS for match — up to 10 retries with 5s delay" means up to 50 seconds of waiting per completed download. If 5 downloads complete simultaneously, there are 5 concurrent 50-second polling loops hammering ABS. The plan does not specify whether `_auto_organize` runs as a detached `asyncio.create_task`. If it runs inline inside `download_monitor`, the monitor loop stalls for up to 50 seconds and misses all other download status transitions during that window.

- **`GET /api/downloads` makes live HTTP calls per request**: This endpoint is polled by the frontend every 5 seconds. Each call fans out to qBittorrent or SABnzbd for live torrent/NZB status. No timeout is specified on these outbound HTTP calls. If qBittorrent is slow or unreachable, the endpoint hangs for the default `httpx` timeout multiplied by the number of active downloads. No circuit breaker, no cached last-known state, no timeout configuration is mentioned.

- **Settings YAML has no file locking**: `app/settings.py` reads and writes `/data/settings.yaml`. If a user saves settings while a background task reads the same file, the concurrent read could get a partially-written YAML and crash or silently load incomplete settings. No atomic write-then-rename pattern is specified.

- **`POST /api/settings` path validation is meaningless in Docker context**: The plan says it "validates paths exist." A path validated inside the container (e.g., `/output`) may exist only because it was created by the container entrypoint, not because the host volume is properly mounted. This gives false confidence. No guidance on what constitutes valid path validation is given.

- **`metadata_cache` has no TTL enforcement and no lookup index**: The table stores `created_at` but has no `expires_at`, no background cleanup task, and no cache invalidation. Hardcover search results will serve stale data indefinitely. There is also no index on `(query, source)` despite that being the obvious lookup key — every cache lookup is a full table scan.

- **No authentication or access control**: The settings page exposes and permits writing API keys. `DELETE` endpoints permanently destroy records. `PUT /api/settings` can change `output_dir` to arbitrary container paths. Anyone reaching port 8743 on the network has full admin access with no credentials required. This is not mentioned as a known limitation or a future concern.

- **`POST /api/books` multi-table insert is not specified as transactional**: The endpoint creates a book AND its requests. If the book insert succeeds but the request insert fails, an orphaned book record exists with no requests. The plan says nothing about wrapping this in a transaction.

### MEDIUM

- **`_split_authors` will misparse many real-world name strings**: Splitting on `, ` will incorrectly split `"Le Guin, Ursula K."` → `["Le Guin", "Ursula K."]`. Real ABS author fields accumulated from user-organised libraries are wildly inconsistent. No test cases, no fallback, no error handling for the split function are specified.

- **`cancelled` appears in the state machine but is forbidden by implementation notes**: The schema section shows `Any state → cancelled (except in_library)` in the state machine diagram. The "What Went Wrong" section then says never use cancelled, always hard-delete. An implementer reading the schema section first will implement `cancelled` as a valid PATCH transition. This contradiction is a guaranteed implementation bug.

- **`ingested_files` pipeline is entirely unspecified**: The table has `extracted_title/author/narrator` and non-prefixed `title/author/narrator` columns, suggesting a two-phase extract-then-confirm pipeline. The plan never describes what populates these columns, what values `status` can take, whether there is a user confirmation step, or when `merged_file_path` is set. This table will be implemented differently by any implementer who reads the plan.

- **The `formats` field in book detail shape has no specified derivation**: `"formats": [{"type": "audiobook", "narrator": "..."}]` is shown in the API response but is not a DB column. It is derived from somewhere — ABS data, `in_library` requests, or the `metadata_links` table. The derivation logic is never specified, guaranteeing inconsistent implementation.

- **`PATCH /api/requests/{id}` status transitions are "validated" but transitions are never listed**: The plan specifies which transitions exist in the state machine but never maps which are user-driven (via PATCH) vs system-driven (background tasks only). Can a user PATCH a `downloading` request to `failed`? Can they reset `completed` to `requested`? Total ambiguity.

- **Cache busting remains manual**: The plan acknowledges manual `?v=N` bumping was a bug in the predecessor and then proposes the exact same mechanism as the solution. No automated content-hash approach is specified. This will cause stale-JS incidents.

- **`POST /api/requests/{id}/download` has no deduplication**: Nothing prevents calling this endpoint twice with the same `guid`. The result is the same torrent added to the download client twice and two download records created. No uniqueness constraint on `downloads.guid` is specified.

- **Enrichment task has no rate limiting or batch size**: `POST /api/enrichment/start` fires one Hardcover API call per un-enriched book. For a 2000-book library, this is 2000 GraphQL requests with no pacing. The plan never specifies delay between calls, maximum concurrency, or what happens on a 429 response.

### LOW

- **`abs_checked_at` column exists in the schema but is never read or written anywhere in the plan**: Either dead schema or an unimplemented feature. Will confuse implementers.

- **No pagination on any list endpoint**: `/api/books`, `/api/authors`, `/api/series`, `/api/requests` all return unbounded lists. A library of 2000+ books returns everything in one response. The plan assumes a small library throughout.

- **`data/` directory contains real API keys and is inside the project directory**: The plan notes this explicitly. If the developer ever initialises a git repository here without a `.gitignore`, the secrets will be committed. No `.gitignore` specification is given anywhere in the plan.

- **`docker-compose.yml` contents are entirely unspecified**: Volume mounts for `/data` and `/output`, environment variables, restart policy, network mode — all left to the implementer. A misconfigured volume mount is the most common Docker Compose failure mode.

- **`POST /api/books/{book_id}/check-abs` match logic is unspecified**: "Fuzzy search ABS" with no similarity threshold defined. No specification of what score constitutes a match.

- **`float(position)` in series sort will raise `ValueError` on non-numeric positions**: The plan says "put non-numeric last" but never specifies the exception handling. A bare `float(position)` call on `"Novella 1"` raises `ValueError` and crashes the sort.

- **`PUT /api/settings` returns `{ ok: true }` regardless of whether the YAML write succeeded**: No read-back verification. A silent permission error on `/data/settings.yaml` would return success while persisting nothing.

- **Pushover settings exist in the YAML schema but no Pushover integration is described anywhere**: No service, no endpoint, no trigger. Either a missing feature or dead configuration that will confuse implementers.

## Summary

The plan is competent and clearly reflects genuine production experience — the normalised schema, explicit state machine, and "learn from this" section all show that real mistakes were made, studied, and documented. The frontend architecture section is unusually detailed for a spec of this type, and the decision to hard-delete rather than soft-cancel requests is the right call. These are genuine strengths.

However, the plan systematically specifies the happy path while leaving almost every failure mode unspecified. The three concurrent background tasks writing to a single SQLite file with no WAL mode, no `busy_timeout`, and no write serialisation is the highest-probability production failure — this will produce `database is locked` errors under any realistic load within days of deployment. Combined with the complete absence of a schema migration strategy, the database layer is the most dangerous part of this plan. The `_auto_organize` pipeline's lack of atomicity means any mid-pipeline crash leaves the system in a state requiring manual filesystem and database repair.

The plan's external-service assumptions are also fragile: the missing-books algorithm makes N Hardcover API calls per page load with no rate limiting or cancellation, the download client polling has no timeout or circuit breaker, and the ABS startup sync has no retry. The absence of any authentication is a significant operational risk. Several tables and features (`ingested_files` pipeline, `enrichment` pacing, `cancelled` state contradiction, `formats` derivation, `abs_checked_at` column) are underspecified to the point where any two implementers would produce incompatible code. These gaps need to be closed before implementation begins.
