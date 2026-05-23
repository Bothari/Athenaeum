# Athenaeum PLAN.md — Compiled Adversarial Review

Three independent reviewers assessed the plan: a **Skeptic** (production failure modes), an **Architect** (system design and schema), and an **Implementer** (practical build friction). Findings are deduplicated and ranked. Where multiple reviewers raised the same issue, it is noted.

Individual reports: [review_skeptic.md](review_skeptic.md) · [review_architect.md](review_architect.md) · [review_implementer.md](review_implementer.md)

---

## CRITICAL

> Issues that will cause data loss, silent failure, or make the system unmaintainable after first deployment.

---

### 1. No schema migration strategy
**Raised by: Skeptic, Architect**

`CREATE TABLE IF NOT EXISTS` provides no path to evolve the schema after go-live. SQLite's `ALTER TABLE` is severely limited. There is no `PRAGMA user_version` check, no migration runner, no versioning at all. This is exactly the pain BookOrganizeClaude suffered — it is deferred again to the first time a column needs adding. The developer will be doing manual `DROP TABLE / recreate` on a live database containing user data.

**Fix before building:** Add a `check_schema_version()` function in `database.py` that compares `PRAGMA user_version` to the expected version and runs any pending migrations.

---

### 2. No SQLite concurrency control — `database is locked` in production
**Raised by: Skeptic**

Three concurrent background tasks (`download_monitor`, `library_sync_task`, `auto_search_task`) plus live API handlers all write to the same SQLite file. The plan never mentions `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout`, or write serialisation. Under any real load this will throw `sqlite3.OperationalError: database is locked` errors that silently swallow state transitions.

**Fix before building:** Enable WAL mode and a busy timeout in `init_db()`:
```python
await db.execute("PRAGMA journal_mode=WAL")
await db.execute("PRAGMA busy_timeout=5000")
```

---

### 3. Background tasks silently die on any unhandled exception
**Raised by: Implementer**

`asyncio.create_task(download_monitor())` will be silently cancelled if `download_monitor()` raises any unhandled exception (database locked, network timeout, etc.). There is no try/except, no supervision loop, no logging. The downloads page returns 200 but nothing ever progresses. This is a day-one production bug that is very hard to diagnose.

**Fix:** Wrap infinite-loop body in `try/except Exception as e: logger.error(...)` and use a supervision pattern that restarts the task.

---

### 4. `_auto_organize` has no atomicity, no rollback, and its call pattern is unresolved
**Raised by: Skeptic, Implementer**

The sequence (move files → scan ABS → poll ABS → update DB) has no error handling between steps. A crash after files are moved but before the DB is updated leaves the system in an unrecoverable state — files gone from source, DB showing old status, and the manual retry will fail because the source no longer exists.

Additionally, the plan never specifies whether `download_monitor()` *awaits* `_auto_organize` (blocking the monitor for up to 50s per completion) or fires it as a detached `create_task` (allowing concurrent organizes to race on the same file). This is architecturally unresolved.

**Fix:** (a) Set `organizing` status before moving, persist the `download_path` being organised, check on retry if file already moved. (b) Explicitly state `asyncio.create_task(_auto_organize(...))` with a guard flag per request_id.

---

### 5. `DELETE /api/requests/{id}` will either orphan rows or fail with a constraint error
**Raised by: Skeptic, Architect**

`downloads` has `request_id TEXT NOT NULL REFERENCES requests(id)` and `ingested_files` has `request_id TEXT REFERENCES requests(id)`. SQLite foreign key enforcement is **OFF by default**. Without `PRAGMA foreign_keys = ON`, deleting a request silently orphans all child rows. If it *is* enabled without `ON DELETE CASCADE`, the delete fails with a constraint error. The plan is silent on both.

**Fix:** Either enable `PRAGMA foreign_keys = ON` in `init_db()` and add `ON DELETE CASCADE` to both child tables, or soft-delete by nulling the foreign key. Choose one and document it.

---

### 6. `POST /api/books` skip-request logic is undefined — hard-delete makes it dangerous
**Raised by: Implementer**

The endpoint creates a book AND its initial requests, returning `_created_requests` / `_skipped_requests` counts. But the plan never defines what makes a request "skipped." After the hard-delete policy: a deleted request leaves no trace, so the skip check sees nothing and allows re-requesting. Whether that is intended is never stated. An implementer will guess wrong and the frontend will show incorrect duplicate-prevention state.

---

### 7. `ingested_files` violates the schema's own design principles
**Raised by: Implementer, Architect**

The table has `extracted_author TEXT`, `author TEXT`, `title TEXT`, `narrator TEXT` — flat strings — despite the plan's stated principle of "no denormalised strings." It is a parallel data model that never maps back to the normalised `books`/`authors` schema. The pipeline that populates it (what fills `status`, `extracted_*` vs non-prefixed columns, `merged_file_path`) is entirely unspecified.

---

### 8. `metadata_links.abs_id UNIQUE` + `book_id UNIQUE` creates a concrete conflict for multi-format books
**Raised by: Skeptic, Implementer, Architect**

The plan says ABS items can have both audiobook and ebook formats, and `_auto_organize` upserts `metadata_links` to set `abs_id`. If the same internal `book_id` is organised from two separate ABS items (audiobook item + ebook item with different IDs), the second upsert fails the `book_id UNIQUE` constraint. Additionally, `abs_id UNIQUE` prevents a book from being linked to two ABS library items, which breaks multi-library setups.

---

## HIGH

> Issues that will cause incorrect behaviour, data inconsistency, or significant rework.

---

### 9. Dual status updates not wrapped in a transaction
**Raised by: Architect**

`download_monitor` updates both `downloads.status` and `requests.status` as separate writes. A crash between them leaves permanently inconsistent state. SQLite supports transactions — they must be used here.

---

### 10. `PUT /api/settings` key format never specified
**Raised by: Implementer**

Settings YAML is nested (`prowlarr.api_key`, `general.output_dir`). The PUT body is `{ settings: { key: value } }` — but are keys flat dotted strings (`"prowlarr.api_key"`)? Nested objects? The plan never says. Frontend and backend will be built inconsistently and the mismatch will only surface at test time.

---

### 11. `cancelled` state in the state machine directly contradicts the deletion policy
**Raised by: Skeptic, Architect, Implementer** *(all three)*

The state machine diagram shows `Any state → cancelled (except in_library)`. The "Request Deletion" section says "Always DELETE the row. Never set status to 'cancelled'." Any implementer reading top-to-bottom will implement the `cancelled` transition and then be forced to rip it out. Remove `cancelled` from the state machine diagram entirely.

---

### 12. `GET /api/downloads` live-polling has no fallback for unreachable download client
**Raised by: Skeptic, Implementer**

The Downloads page polls every 5 seconds. Each call fans out to qBittorrent/SABnzbd with no specified timeout. If the client is slow or down, the endpoint hangs (or throws) and the entire page breaks. No circuit breaker, cached last-known state, or timeout configuration is mentioned.

---

### 13. `GET /api/series/{id}/missing` makes N+1 Hardcover API calls with no rate limiting
**Raised by: Skeptic, Architect, Implementer** *(all three)*

One `get_series()` call + one `search(title)` per book = 21 sequential Hardcover API calls for a 20-book series. Discworld has 41 books. No rate limiting, no backoff, no 429 handling is specified. The plan says "the workaround is correct — don't try to simplify it," which means the N+1 pattern is mandatory but all failure handling is left undefined.

---

### 14. `author_links` upsert is underspecified and will lose linked IDs
**Raised by: Skeptic, Architect, Implementer**

`author_links` has two UNIQUE columns (`hardcover_author_id`, `abs_author_id`). SQLite's `INSERT OR REPLACE` on a multi-UNIQUE-constraint table deletes and re-inserts, silently losing the non-conflicting linked ID. The `_get_or_create_author()` upsert logic is never described.

---

### 15. `POST /api/books` + `POST /api/requests` have no shared deduplication contract
**Raised by: Implementer**

`expandRequestForm` calls `/api/books` when creating a new book (which internally creates requests) and `/api/requests` when the book already exists. Duplicate-prevention logic must be identical in both paths, but the plan specifies no shared service layer for this. An implementer will implement one path correctly and leave the other inconsistent.

---

### 16. Settings YAML has no file locking
**Raised by: Skeptic**

Concurrent reads (background tasks) and writes (user saving settings) on `/data/settings.yaml` with no atomic write-then-rename pattern. A partially-written YAML will crash any reader that loads it mid-write.

---

### 17. `library_sync` has no update path — ABS metadata changes are silently ignored forever
**Raised by: Architect**

The sync logic skips any item already present in `metadata_links` by `abs_id`. Once an item is synced, title corrections, narrator updates, and new formats added in ABS are never picked up. No re-sync or refresh mechanism is described.

---

### 18. `renderTable` sort/filter state is unspecified
**Raised by: Implementer**

Every list page uses this shared function with "sortable columns and text filter." Sort state must live somewhere (component variable? URL param?), filter must debounce, re-render must not cause a full page reload. None of this is described. The filter state will be lost on SPA navigation.

---

### 19. Enrichment task state is in-memory only — lost on restart
**Raised by: Implementer**

`GET /api/enrichment/status` returns `{ running, processed, total, current_book }` from in-memory state. A Docker restart mid-enrichment silently abandons it with no way to detect or resume.

---

### 20. Dockerfile and `requirements.txt` contents are never specified
**Raised by: Implementer**

Phase 1 Item 1 is "Dockerfile and requirements.txt" but neither is described. Missing at minimum: `uvicorn` (app won't start without it), `python-multipart` (FastAPI form data requirement), base image choice, working directory, CMD.

---

## MEDIUM

> Design gaps that will cause confusion, inconsistency, or require rework mid-build.

- **`formats` field in book detail shape is not backed by any table**: Must be derived — from `in_library` requests or ABS — but the plan says not to use request status to infer library presence. Never resolved. (Skeptic, Implementer, Architect)

- **`metadata_cache` table is a dead schema**: Defined, never read from or written to anywhere in the plan. No TTL, no eviction, no `(query, source)` index. Either specify or remove. (Skeptic, Architect, Implementer)

- **`PATCH /api/requests/{id}` transition validation never listed**: "Status transitions validated" but which transitions are user-accessible vs system-only is never stated. Can a user reset `downloading` to `requested`? (Skeptic, Implementer)

- **`ingested_files` pipeline is entirely unspecified**: What populates `extracted_*` columns? What are valid `status` values? Is there a user confirmation step? Any two implementers will produce incompatible code. (Skeptic)

- **Cache busting is still manual `?v=N`**: Same mechanism that failed in BookOrganizeClaude. Without `Cache-Control: no-cache` on the HTML response, browsers may cache the HTML and ignore the `?v=N` entirely. (Skeptic, Implementer)

- **`book_search.py` result has `all_series` but API shape only exposes one `series` string**: When a book belongs to multiple series, the API collapses to one. How to pick which series is never specified. (Implementer)

- **`GET /api/book/detail` is not assigned to any build phase**: Present in the route spec, missing from the build order. Will be discovered missing during frontend work. (Implementer)

- **`POST /api/requests/{id}/organize` manual retry fails for the same reason as auto-organize**: Reads `download_path` from DB — if that path is wrong, no way to supply a corrected path via the endpoint. (Implementer)

- **`confirmAction()` DOM lifecycle not described**: SPA re-renders wipe confirmation state. Multiple rows in confirm-state simultaneously is unhandled. (Implementer)

- **`advanced_search` "grouping by series" setting is unspecified**: What does "grouped" mean in a flat JSON array? The plan never says. (Implementer)

- **`POST /api/requests/{id}/download` has no deduplication on `guid`**: Same torrent can be added twice, creating two download records. No UNIQUE constraint on `downloads.guid`. (Skeptic)

- **Enrichment task has no rate limiting or batch size**: 2000-book library → 2000 Hardcover API calls with no pacing. (Skeptic)

- **Service instantiation pattern never described**: Are services module-level singletons? Per-request instances? FastAPI `Depends()`? Routes import them differently depending on who implements them. (Implementer)

---

## LOW

> Minor issues that are easily fixable but worth noting.

- **`abs_checked_at` column is never written by any described code path** — orphaned schema column. (All three)
- **`float(position)` in series sort will raise `ValueError`** on `"Novella 1"` — the plan says "put non-numeric last" but never shows the try/except. (All three)
- **No pagination on any list endpoint** — unbounded returns for 2000+ book libraries. (Skeptic)
- **`data/` directory with real API keys has no `.gitignore` specification** — credential commit risk if a repo is initialised here. (Skeptic)
- **Pushover is configured in YAML but never used** — dead configuration confuses implementers. (Skeptic, Implementer)
- **`docker-compose.yml` contents entirely unspecified** — volume mounts, restart policy, network mode all left to implementer. (Skeptic)
- **Dashboard (`/#/`) has no nav item** — no way to navigate back except logo (unspecified) or URL bar. (Implementer)
- **`_split_authors` is case-sensitive** — `" AND "` uppercase won't split. (Implementer)
- **TEXT UUIDs vs INTEGER rowids** — unnecessary SQLite B-tree pessimisation. (Architect)
- **`GET /api/status` response shape undefined** — which statuses are keys? What about the removed `cancelled`? (Implementer)
- **`author_links` / `series_links` UNIQUE constraints on nullable columns block pen-name / multi-ID scenarios** — one external-ID row per author is too restrictive. (Architect)
- **Comma-separated `library_id` string should be a YAML list** — unnecessary custom parsing. (Architect)
- **No auth acknowledgement** — reasonable for self-hosted, but not even noted as a known limitation. (Skeptic, Architect)

---

## Consensus: Top Fixes Before Writing Any Code

The following are rated CRITICAL by 2+ reviewers and should be resolved in the plan before implementation begins:

| # | Fix | Reviewers |
|---|-----|-----------|
| 1 | Add `PRAGMA user_version` migration system to `database.py` | Skeptic, Architect |
| 2 | Specify `PRAGMA journal_mode=WAL` + `busy_timeout` in `init_db()` | Skeptic |
| 3 | Add try/except supervision loop around all background tasks | Implementer |
| 4 | Resolve `_auto_organize` call pattern (await vs create_task) + add partial-move recovery | Skeptic, Implementer |
| 5 | Add `ON DELETE CASCADE` to `downloads` and `ingested_files`, enable `PRAGMA foreign_keys=ON` | Skeptic, Architect |
| 6 | Remove `cancelled` from the state machine diagram entirely | Skeptic, Architect, Implementer |
| 7 | Specify `PUT /api/settings` key format (flat dotted strings vs nested object) | Implementer |
| 8 | Define `_skipped_requests` criteria in `POST /api/books` | Implementer |
| 9 | Resolve `metadata_links` multi-format / multi-library constraints | Skeptic, Implementer, Architect |
| 10 | Wrap `download_monitor` dual-status update in a transaction | Architect |
