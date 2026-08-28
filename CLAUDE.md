# Athenaeum — Claude Code Instructions

## Project Overview

Athenaeum is a self-hosted book management app. Full specification is in `docs/dev/PLAN.md`.
Read it entirely before writing any code. It is the single source of truth.

---

## Build & Run

The `athenaeum` container runs **released images** (`ghcr.io/bothari/athenaeum:latest`),
not the working tree. Editing code and restarting it does nothing — a change reaches
it only by being tagged and published.

```bash
# Update to the newest release
docker compose pull athenaeum && docker compose up -d athenaeum

# Logs / stop
docker logs -f athenaeum
docker compose stop athenaeum
```

The app serves on port **8741**. Data persists in the mounted data directory.

To pin or downgrade, set the tag explicitly (`:1.0.0`); `:testing` is the dogfood
branch. See "Versioning and branches" below.

---

## Development Workflow

- `settings.yaml` in the data directory holds real API keys — never commit `data/`
- `athenaeum.db` is SQLite — inspect with `sqlite3 <data-dir>/athenaeum.db`
- Logs are the primary debugging tool

### Testing a change

Unreleased code is **never** tested by restarting the live container. In order of preference:

1. **The test suite** — fastest, and required before pushing.
2. **A throwaway container built from the working tree**, pointed at a *copy* of the
   data directory. This is the only safe way to exercise a migration: clone the data
   dir, run the new build against the clone, verify, then discard. Never point an
   unreleased build at the live data directory.
3. **`athenaeum-dev`**, which builds from a separate worktree with live-reload mounts.
   Check which branch that worktree is on before assuming it reflects your change.

Claude must not report a change as verified on the strength of a live-container
restart — that only ever proves the last *release* still works.

### Running Tests

Tests only need to be run before pushing to GitHub. Run them inside the project virtualenv:

```bash
.venv/bin/python -m pytest tests/ -v
```

### Cache Busting

Nothing to do by hand. Vite hashes every asset filename, so a changed file is a
changed URL. The shell that references them is served with `Cache-Control: no-cache`,
so browsers always revalidate it and pick up the new hashes.

`static/` is build output, not source — it is populated by the frontend build stage
in the Dockerfile and is empty in a fresh checkout. Never edit anything in it.

---

## Versioning and branches

Tags follow semver (`major.minor.patch`). Every `v*` tag is a real release:

- patch (`v1.0.1`) — bugfixes
- minor (`v1.1.0`) — new features
- major (`v2.0.0`) — breaking changes

**The number describes the product, not the diff.** Size of the internal change is
irrelevant — the frontend rewrite replaced every line of the UI and still ships as a
minor, because a user who upgrades sees the same app. Reserve a major for a release
where the app visibly becomes a new thing, or where upgrading breaks something for
the user.

Do not let a project codename leak into the version. "v2" is the name of the frontend
rewrite (`docs/V2_FRONTEND_PLAN.md`); it ships as `v1.1.0`.

### Branches

| branch | image tag | role |
|--------|-----------|------|
| `main` | `:latest`, `:x.y.z`, `:x.y` | always releasable; tag it to publish |
| `topic/*` | — | one change each, however long it takes |
| `dogfood` | `:testing` | throwaway integration branch |

A topic branch graduates to `main` **on its own**, via PR, and is then tagged. It
never reaches main by way of `dogfood`.

`dogfood` exists to answer "what do all the in-flight changes look like together".
It is rebuilt, never merged into anything, and never branched off — which is what
lets a risky topic sit for months without blocking releases, and why force-pushing
it is safe:

```bash
scripts/rebuild-dogfood.sh          # main + every topic/* branch
git push -f origin dogfood          # publishes :testing
```

Note that you dogfood the *combination* but ship the *individual* branch, so a
topic is not proven in isolation by dogfooding. The PR's CI run against main is
what covers that.

---

## Git Commits

All commits must end with a co-author trailer naming the model that actually wrote
the commit:

```
Co-Authored-By: <model name> <noreply@anthropic.com>
```

For example `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Use your own
model name — do not copy a name from an older commit, and never attribute work to a
model that did not write it.

Commit messages should be concise and describe *why*, not just *what*.
Use present tense. Example: "Add WAL mode to prevent database locking under load"

**When to commit:** Wait for explicit confirmation from the user before running
`git commit`. Stage changes and summarise what will be committed, then wait for
the go-ahead.

**Never push to GitHub** without the user's explicit instruction. `git push` is
off-limits unless the user asks for it in that specific message.

---

## ABS API Usage

ABS runs locally on the same Docker network — treat it like a local database call, not a remote API.

- **Always fetch full items** via `GET /api/items/{id}` for sync. The list endpoint (`/api/libraries/{id}/items`) returns minified items that omit series IDs, author IDs, and ebookFile. Never rely on minified list data for anything that needs to be normalised.
- **Concurrency is fine** — use `asyncio.gather` with a semaphore (10–20 concurrent) when fetching many items. There is no rate limit concern.
- **Prefer IDs over name-matching** wherever ABS provides them. Series, authors, and narrators all have stable IDs in full item responses. Store these IDs in the `_links` tables (`abs_series_id`, `abs_author_id`) so we can do exact lookups rather than fuzzy name matching.

---

## Code Conventions

These are defined in `docs/dev/PLAN.md` and must be followed precisely:

- **Services** are instantiated per-request (not singletons). Read current settings at call time.
- **Database** access goes through `get_db()` only — never open connections directly.
- **Settings** access goes through `get_settings()` / `save_settings()` only — never read the YAML directly.
- **Deduplication** for request creation always goes through `_create_request()` — never inline.
- **INSERT OR REPLACE** must never be used on `author_links` or `series_links` — use INSERT OR IGNORE + targeted UPDATE.
- All multi-table state updates must be wrapped in a transaction.
- Background task bodies must be wrapped in try/except — exceptions are logged, never silently swallowed.

---

## Schema Changes

Never use bare `CREATE TABLE IF NOT EXISTS`. All schema changes go through the migration system in `app/database.py` (PRAGMA user_version blocks). See `docs/dev/PLAN.md` → Database section.

---

## Style Rules

- **No emojis** anywhere — not in docs, code comments, commit messages, or any project file.

---

## Frontend (v2)

The UI is being rewritten in Svelte. Stack: SvelteKit 2 + Svelte 5 (runes) +
TypeScript + `adapter-static` in SPA mode, built by Vite into `static/` and served by
the existing FastAPI catch-all. No Node server at runtime. No Tailwind — styling uses
scoped component `<style>` blocks with shared tokens as CSS custom properties in
`src/app.css`. Full plan in `docs/V2_FRONTEND_PLAN.md`.

### Mobile: never zoom the page on text-field focus

This is a hard requirement, not a preference. It was painful to get right in v1 and
must not regress.

iOS Safari zooms the viewport when a focused text field's **computed** font-size is
below 16px. Therefore:

- **Never set `font-size` below 16px on `input`, `select`, `textarea`, or any class
  applied to one.** This includes rem values that resolve below 16px — `0.9rem` is
  14.4px and WILL zoom.
- To make a field look smaller, reduce **padding, height, or width**. Never font-size.
- **Never** suppress zoom with `user-scalable=no` or `maximum-scale=1` in the viewport
  meta. That works by disabling pinch-zoom entirely, which breaks accessibility. The
  font-size approach is the only acceptable fix.
- Scoped component styles make this more dangerous than in v1: a local rule silently
  beats the global one in `src/app.css` and nothing warns you.
- `npm run check:zoom` enforces this and must stay in CI.

v1 hit this repeatedly — `.fmt-narrator-input` and `.search-input-main` each had to
re-declare `font-size: 16px` after a smaller value crept in. Do not relearn it.

Also keep `touch-action: manipulation` on tappable controls to kill the 300ms
double-tap-zoom delay.

### No monolith

v1's entire UI was one 4,506-line `static/app.js` with 158 `innerHTML` assignments.
Avoiding a repeat is a primary goal of the rewrite, not a nice-to-have.

- **One route per file** under `src/routes/`, using SvelteKit's file-based routing.
  Never a central router or dispatch table.
- **Any component over ~200 lines is a smell** — extract sub-components. Route files
  should mostly compose components and handle data loading.
- **Shared UI goes in `src/lib/components/`** and is reused. If you find yourself
  writing a second variant of an existing card/table/state component, extend the
  existing one instead. v1 had three near-duplicate card renderers.
- **API calls go through `src/lib/api/`**, one module per backend router, with typed
  responses. Never call `fetch` directly from a component.
- **Shared state goes in `src/lib/stores/`** using runes. Never module-level mutable
  `let` bindings as de facto globals, which is how v1 handled auth state.

---

## Progress Tracking

`docs/dev/PROGRESS.md` tracks build progress against the phases in `PLAN.md`.

**Update it whenever:**
- A phase or sub-task is completed — check the box and add a completion date
- A phase is started — note it as in progress
- Post-phase polish or fixes are done — add them as a named block (as with "Mobile UI polish")

Keep entries concise. The git log has the detail; PROGRESS.md is the at-a-glance view.

---

## Attribution

This project is being developed with Claude Code, across successive Claude models.
Per-commit attribution lives in the git log's co-author trailers, which is the
authoritative record — this file does not name a specific model.

The development process — including the original spec, adversarial review, and review-driven amendments — is documented in `docs/`.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
