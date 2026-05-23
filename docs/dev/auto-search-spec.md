# Auto-Search and Auto-Download — Specification

## Goal

Remove the need to manually pick a Prowlarr result for every request. When a request is created or approved, Athenaeum should automatically search, rank results, and send the best one to the download client — without any user intervention unless quality thresholds aren't met. A scheduled task handles items that had no results at request time (e.g. books not yet available) and retries them periodically.

This feature must be reliable and conservative: it is better to do nothing than to grab the wrong thing.

---

## Trigger points

### 1. On request creation / approval

When a request enters the `requested` state (either directly for admin requests, or after admin approval for user requests), an auto-search is triggered immediately if:

- Prowlarr is configured
- Auto-search is enabled in settings
- The request is not already in a terminal state

### 2. Scheduled task

A new scheduled task (`auto_search`, cron configurable, default `0 */6 * * *`) runs over all requests in `requested` state and triggers the same search-rank-send flow. This covers:

- Items that had no results when the request was created (too new, not yet indexed)
- Items that were released since the last run
- Requests that were manually created without an immediate search

A request that has failed auto-search more than N times (configurable, default 10) should be skipped to avoid hammering Prowlarr forever. A `search_attempts` counter and `last_searched_at` timestamp handle this.

---

## Result filtering (hard filters, applied before ranking)

Before ranking, results are filtered out if they fail any of these:

1. **Format**: extension not in `allowed_audiobook_formats` / `allowed_ebook_formats`
2. **Series pack exclusion**: result title contains series-pack indicators — patterns like `Complete Series`, `Box Set`, `Books 1-N`, `Omnibus`, or contains multiple book titles separated by `/` or `&`. This is a heuristic; false positives are acceptable — it is better to skip a valid single-book result with an unusual title than to accidentally grab a series pack for a single-book request. Exact match patterns TBD during implementation.
3. **Minimum seeders**: for torrent results, seeder count must be ≥ configured minimum (default: 1, set to 0 to disable). NZB results are not subject to this filter.

Results that pass all filters proceed to ranking.

---

## Result ranking

Ranking is a multi-key sort. The user configures an ordered priority stack in Settings. Each criterion is either ascending or descending. The result with the best composite rank is selected.

### Configurable criteria

| Criterion | Type | Direction | Notes |
|---|---|---|---|
| **Format** | Enum | Fixed | Position in `allowed_formats` list — index 0 is most preferred. Reuses the existing format order. |
| **Seeders / peers** | Integer | Descending (more = better) | Torrent only; NZB results receive a fixed high score for this criterion so they are not penalised |
| **Size** | Bytes | User choice: prefer larger or prefer smaller | Larger often means better quality for audiobooks; smaller may be preferable for ebooks or bandwidth-constrained users |
| **Age** | Days since indexed | User choice: prefer newer or prefer older | Newer can mean a recently seeded release; older can mean a well-established one with long-term seeds |

### Stack configuration

The stack is an ordered list of criteria. The first item is the primary sort key; ties break on the second, and so on. The user can:

- Reorder criteria by dragging
- Enable or disable individual criteria
- Configure direction (where applicable)
- Set the minimum seeder threshold

Format is always available as a criterion. Seeders, size, and age are all optional — if disabled, they are ignored in ranking.

### Ranking algorithm

Each result produces a tuple of scores based on the stack order. Results are sorted by these tuples. The top-ranked result that exists after filtering is selected.

Example stack: `[Format, Seeders (desc), Size (prefer larger)]`

- Result A: m4b (score 0), 45 seeders, 800 MB
- Result B: mp3 (score 1), 120 seeders, 400 MB
- Result C: m4b (score 0), 12 seeders, 500 MB

Sorted: A > C > B (format is the primary key; A beats C on seeders; both beat B on format).

---

## Auto-search flow

```
request enters `requested` state
  → is Prowlarr configured and auto-search enabled? → no: stop
  → increment search_attempts, set last_searched_at
  → search Prowlarr with title + author query
  → apply hard filters (format, series exclusion, min seeders)
  → any results pass? → no: log "no results", stay `requested`
  → rank results, select top result
  → send to download client
  → update request status to `snatched`
  → log event with selected result details
```

On failure at any step (Prowlarr unreachable, download client error, etc.), log the error, leave status as `requested`, and let the scheduled task retry.

---

## Series pack exclusion — detail

When searching for a single book, Prowlarr will often return series pack torrents that match on the author name. These must be excluded. Exclusion is heuristic-based:

**Patterns to reject (case-insensitive, checked against result title):**
- `complete series`
- `complete collection`
- `box set`
- `omnibus`
- `books \d+[-–]\d+` (e.g. "Books 1-7")
- `\d+ books` (e.g. "7 Books")
- `the complete` followed by a series name
- Multiple ` & ` or ` / ` separators suggesting multiple titles

These patterns will catch the majority of series packs. False positives (a single book with "Complete" in the title) are acceptable — the user can always fall back to manual selection.

---

## Settings additions

### Auto-search tab (or section within General)

- **Enable auto-search** — master toggle
- **Search on request** — search immediately when a request is created/approved (default: on)
- **Max search attempts** — give up after N failed searches per request (default: 10)
- **Minimum seeders** — filter out torrent results below this threshold (default: 1)

### Result ranking stack

A draggable list of criteria cards. Each card:
- Drag handle on the left
- Criterion name and description
- Direction toggle where applicable (prefer larger/smaller, prefer newer/older)
- Enable/disable toggle

Stored in `settings.yaml` as:

```yaml
auto_search:
  enabled: false
  search_on_request: true
  max_attempts: 10
  min_seeders: 1
  ranking:
    - criterion: format
      enabled: true
    - criterion: seeders
      enabled: true
    - criterion: size
      enabled: true
      prefer: larger
    - criterion: age
      enabled: false
      prefer: newer
```

---

## Database changes

`requests` table gains two new columns:

| Column | Type | Description |
|---|---|---|
| `search_attempts` | INTEGER DEFAULT 0 | Number of auto-search attempts made |
| `last_searched_at` | TEXT | ISO timestamp of most recent auto-search attempt |

Migration in the existing user_version block system.

---

## Request history / events

All auto-search activity is logged to `request_events`:

| Event type | When |
|---|---|
| `auto_search_started` | Search triggered |
| `auto_search_no_results` | Prowlarr returned results but all filtered out |
| `auto_search_failed` | Prowlarr or download client error |
| `auto_search_snatched` | Result selected and sent to download client, includes result title, indexer, format, size, seeders |

---

## What is NOT in scope for v1

- Automatic approval of user requests before searching (users still require admin approval)
- Per-request ranking overrides
- Preferred indexer weighting
- Smart backoff (exponential retry delay) — flat attempt counter is sufficient initially

---

## Quality bar

This feature should not ship until:

1. Series pack exclusion is reliable enough that it does not grab packs for single-book requests in manual testing across a representative set of books
2. The ranking logic produces sensible results across mixed torrent/NZB result sets
3. The `search_on_request` path does not noticeably delay the request creation API response (run in a background task, not inline)
4. Failed auto-searches are clearly visible in the request event log so users can diagnose why nothing was grabbed
