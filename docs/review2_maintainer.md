# Maintainer Review — Athenaeum PLAN.md (Round 2)

## Persona
I deployed this app and I'm responsible for keeping it running. I need to know it'll restart cleanly, that I can diagnose problems from logs, that upgrades won't break my database, and that I'm not slowly accumulating storage or state that will bite me later.

---

## Findings

### HIGH

- **No health endpoint — Docker healthcheck is impossible**: The plan specifies a `restart: unless-stopped` policy in `docker-compose.yml` but never defines a health check. Without a `GET /health` or `GET /api/health` endpoint, Docker has no way to know if the app is up and serving. The container will be reported healthy as long as the process is running — even if the database is locked, the ABS connection is broken, or the app is in an error loop. A simple `{ ok: true }` endpoint would allow a `HEALTHCHECK` directive in the Dockerfile and `healthcheck:` in compose.

- **Sync and enrichment status is lost on restart**: `GET /api/sync/status` returns `{ running, last_run, last_result }`. This state lives in memory (module-level variables in `main.py` or the sync service). After a Docker restart, `last_run` becomes null and `last_result` is gone. A user who asks "when did the library last sync successfully?" after a restart gets no answer. `last_run` and `last_result` should be persisted — either in the DB (a `sync_log` table) or in settings.yaml — so restart doesn't erase operational history.

- **Enrichment feature is referenced but its routes are absent from the spec**: The first-round compiled review raised enrichment rate-limiting. The current PLAN.md references `POST /api/enrichment/start` and `GET /api/enrichment/status` (in the first-round review; these were carried forward into the compiled findings as issue #19). But the current route specification has no enrichment routes at all — they don't appear in `app/routes/books.py`, `sync.py`, or anywhere. Either the enrichment feature has been removed (in which case the Phase 7 build item "Enrichment progress" should be deleted) or it was accidentally omitted from the routes spec. This ambiguity will cause confusion during Phase 6/7 build.

### MEDIUM

- **No log level configuration**: The plan describes a supervised background task pattern with `logger.error(...)` calls, but the logging configuration is never specified. What is the default log level? Is there a way to enable DEBUG logging without a code change? For diagnosing production issues (e.g., why did ABS linking fail for this book?), the difference between ERROR and DEBUG logging is enormous. At minimum, a `LOG_LEVEL` environment variable in the Dockerfile or compose file should be described.

- **`merge_jobs` rows accumulate with no cleanup path beyond cascade delete**: `merge_jobs` rows are cascade-deleted when the parent request is deleted. But for successfully completed books (status `in_library`), there is no reason to delete the request — so `merge_jobs` rows for all merged books persist forever. For a large audiobook library with merge enabled, this table will grow indefinitely. The plan should specify a retention policy (e.g., delete merge_jobs rows after a book reaches `in_library`) or explicitly note this as acceptable.

- **`metadata_cache` cleanup task is unspecified**: The table now has `expires_at` and an index on it. But nothing in the plan describes who deletes expired rows. `cache_refresh_task` overwrites stale entries on refresh — but only for entries linked to books the app knows about. Orphaned cache entries (from books deleted after being cached, or series that were searched but never added) will never expire in practice. A nightly sweep (`DELETE FROM metadata_cache WHERE expires_at < now()`) should be described somewhere.

- **Cron expressions in settings.yaml have no validation**: A user who saves a malformed cron expression (`"0 2 * * * *"` — six fields instead of five) will cause `croniter` to raise on `_wait_until_next()`, killing that background task until the next restart. The plan says `PUT /api/settings` rejects unknown top-level keys with 400, but there's no mention of validating cron expression syntax. One bad paste from the UI silently breaks scheduled tasks.

### LOW

- **No database backup guidance**: `athenaeum.db` is mounted at `./data/athenaeum.db`. A schema migration bug or an accidental `DELETE` with no WHERE clause can corrupt or empty the database. The plan says nothing about backups — not even a note that users should back up `./data/` before upgrades. A line in the deployment section would be enough.

- **The output volume path is a placeholder**: `docker-compose.yml` shows `/path/to/output:/output` as the output volume. This is a template, not a real value. A user who copies the compose file without editing it will start an app that silently fails to organise any downloads (the path doesn't exist). A comment — `# Replace /path/to/output with your actual audiobook library path` — would prevent a common first-deploy failure.

- **SCHEMA_VERSION constant is in `database.py` but nothing enforces it stays in sync**: The pattern is `SCHEMA_VERSION = 1` with `if current < 1` guards. If a developer adds a migration (setting `SCHEMA_VERSION = 2`) but forgets to add the corresponding `if current < 2` block — or vice versa — the migration silently does nothing (or the wrong thing). The pattern works but is easy to get out of sync. A note in CLAUDE.md or a comment in database.py saying "always bump SCHEMA_VERSION and add the if-block together" would prevent the most common mistake.
