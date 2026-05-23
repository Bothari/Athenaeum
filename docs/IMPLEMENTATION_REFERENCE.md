# Athenaeum — Implementation Reference

This document describes how BookOrganizeClaude (the predecessor) implemented several non-obvious subsystems. Use it as authoritative guidance when building the equivalent in Athenaeum. Where BookOrganizeClaude made mistakes they are called out explicitly.

---

## 1. Hardcover Metadata (GraphQL API)

### Endpoint and auth

All queries go to `https://api.hardcover.app/v1/graphql` via POST with `Content-Type: application/json`. The API key is sent as `Authorization: Bearer <key>`. The key is optional for public data but required for rate-limit headroom.

### The two-step search pattern

Hardcover's search endpoint returns only IDs, not full book data. A second query is always needed:

```
Step 1 — search(query, query_type: "books", per_page: 50, sort: "users_count:desc")
          → returns { ids: [int, ...] }  (ordered by popularity)

Step 2 — books(where: {id: {_in: $ids}})
          → returns full book objects
```

Preserve the order from Step 1 when building results — `books()` does not return items in the same order as the ID list.

### The series-lookup problem (CRITICAL)

`series_by_pk(id: $id)` returns one entry per position in the series, but the book it returns for each position is often an obscure, low-`users_count` edition (e.g. a foreign translation). This caused visibly wrong cover art and metadata.

**The fix**: For the "missing books in series" feature, fetch the series only to get the canonical list of positions and titles. Then, for each book in the series, call `search(title)` and pick the most popular result that matches that title. Keep the `series_position` from the series endpoint but all other metadata (cover, description, ISBN, etc.) from the search result.

**Best-edition selection algorithm** (pick most popular matching edition):
1. Sort candidates by `users_count DESC, ratings_count DESC, rating DESC`
2. Apply language filter: prefer editions whose `language` matches `preferred_language` setting; drop entries with a known non-preferred language (pass through entries with no language set)
3. Take the first result

### Normalised book shape

Every Hardcover book object is normalised to this flat dict before leaving `book_search.py`:

```python
{
    "title": str,
    "subtitle": str,
    "author": str,           # primary author name only
    "author_id": str,        # Hardcover author ID
    "narrator": str,         # first narrator from contributions
    "description": str,
    "cover_url": str,        # from cached_image.url
    "isbn": str,             # from best edition (isbn_13 preferred)
    "asin": str,
    "pages": int,
    "publisher": str,
    "published_year": str,
    "language": str,
    "genres": [str],         # from cached_tags["Genre"]
    "rating": float,
    "rating_count": int,
    "users_count": int,      # total users who've read this — primary sort key
    "series": str | None,    # featured series name
    "series_id": str | None, # Hardcover series ID (numeric, stored as string)
    "series_position": str,  # "1", "2.5", etc. (string to handle decimals)
    "is_compilation": bool,  # True if position covers multiple books (e.g. "1-3")
    "compilation_details": str,
    "all_series": [{"name": str, "id": str}],  # all series for fuzzy matching
    "metadata_source": "hardcover",
    "metadata_id": str,      # Hardcover book ID
    "slug": str,
    "metadata_url": str,     # https://hardcover.app/books/{slug}
    "hardcover_url": str,
}
```

### Series position format

`series_position` is always a string. It can be:
- `"1"`, `"2"`, `"10"` — regular position
- `"2.5"` — novella between books
- `"1-3"` — compilation spanning multiple books (`is_compilation=True`)
- `"1, 3"` or `"1 & 2"` — compilation (`is_compilation=True`)
- `""` — unknown/unnumbered

When sorting positions numerically: `float(series_position)` — handle `ValueError` for non-numeric values by placing them last.

### Compilation detection

A book is a compilation if:
- `book_series.compilation` is truthy, OR
- `details` or `position` string contains a comma or ampersand, OR
- `details` or `position` matches `\d+\s*-\s*\d+` (a range)

For sorting, compilations sort after their last included book: `"1-3"` sorts after position `3`.

### GraphQL fields to request

The `BOOK_FIELDS` fragment (used in all queries) should include:
```
id, slug, title, subtitle, description, release_year, pages, audio_seconds,
rating, ratings_count, users_count, cached_image, cached_contributors,
cached_tags,

contributions(order_by: {id: asc}) {
  contribution
  author { id name }
}

book_series {
  position details featured compilation
  series { id name }
}

editions(order_by: {users_count: desc}, limit: 5) {
  isbn_10 isbn_13 asin edition_format pages audio_seconds
  release_date release_year
  language { language }
  publisher { name }
}
```

### Advanced search

`advanced_search(title, author, series)` uses Hasura filter syntax directly on the `books` table (`_ilike` for case-insensitive partial match). For author queries, strip periods and join name parts with `%` wildcards so `"James S. A. Corey"` becomes `"%James%S%A%Corey%"`. This handles period/spacing variants.

When searching by series name and a book belongs to multiple series, emit one result per matching series (not one per book), so the series grouping is correct.

---

## 2. AudiobookShelf (ABS) Integration

### Auth

Every request needs `Authorization: Bearer <abs_api_key>`. Base URL comes from `abs_url` setting (strip trailing slash).

### Key endpoints used

| Purpose | Endpoint |
|---|---|
| Test connection | `GET /api/me` |
| List libraries | `GET /api/libraries` |
| List all items in a library | `GET /api/libraries/{lib_id}/items?limit=0` |
| Search a library | `GET /api/libraries/{lib_id}/search?q={query}&limit=25` |
| Get single item | `GET /api/items/{item_id}` |
| Get item cover | `GET /api/items/{item_id}/cover` |
| Trigger scan | `POST /api/libraries/{lib_id}/scan` |

`limit=0` on the items endpoint returns all items (not paginated).

### Multi-library support

`abs_library_id` setting can be a comma-separated list of library IDs. All fetch functions iterate over every library ID and merge results.

### ABS item structure (normalised)

```python
{
    "abs_id": str,
    "title": str,
    "author": str,           # primary author string (may be "Author1, Author2")
    "abs_url": str,          # {base_url}/item/{abs_id}
    "cover_url": str,        # {base_url}/api/items/{abs_id}/cover
    "description": str,      # HTML-stripped
    "genres": str,           # comma-joined genre list
    "series_list": [{"name": str, "position": str}],
    "formats": [             # one entry per format present
        {"type": "audiobook", "format": "M4B", "narrator": "..."},
        {"type": "ebook",     "format": "EPUB", "narrator": ""},
    ]
}
```

A single ABS item can have both an audiobook and an ebook format. Always check `formats` array — never assume one format per item.

### Format detection

```python
# audiobook: media.audioFiles or media.numAudioFiles
# ebook: media.ebookFile or media.ebookFormat
```

Audio format string comes from `audioFiles[0].metadata.ext`. Ebook format from `ebookFile.metadata.ext` or `ebookFormat`.

### Series parsing from ABS

ABS stores series in `metadata.seriesName` as a string like `"Honor Harrington #9"` or `"Series A #1, Series B #2"`.

Parsing logic:
1. Split on comma for multiple series
2. For each part, regex-match position patterns: `#N`, `Book N`, `Vol N` (where N is `\d+(?:\.\d+)?`)
3. Strip the position marker from the name
4. Build `{"name": str, "position": str}` entries

Newer ABS versions may also have a `metadata.series` array of `{name, sequence}` objects — check that first, fall back to `seriesName` string.

### Fuzzy matching for library checks

When checking if a book exists in ABS (duplicate prevention), search by title only (ABS search doesn't handle combined title+author well). Then filter results by fuzzy author match:

```python
def _fuzzy_match(query, target):
    # Normalise: lowercase, strip periods and spaces
    q = query.lower().replace(".", "").replace(" ", "")
    t = target.lower().replace(".", "").replace(" ", "")
    return q in t or t in q
```

This handles `"S. A. Corey"` vs `"S.A. Corey"` etc.

### Duplicate prevention (library_formats)

**The correct approach**: When displaying search results, check the `requests` table for existing requests. For books with `status = 'in_library'`, also query ABS directly (`get_item_by_id`) to get the definitive `formats` array. This tells the UI which formats already exist in the library.

**Do NOT** check the `requests` table alone — deleted requests leave no trace and old cancelled rows can block re-requesting.

**Do NOT** mark deleted requests as `status='cancelled'` — hard-delete them. Cancelled rows interfere with duplicate checks.

---

## 3. Library Sync (ABS → Database)

The sync process (`library_sync.sync_library()`) runs on startup (after 30s delay) and on a configurable interval (default 12 hours). It can also be triggered manually.

### Sync algorithm

```
For each ABS item:
  1. Check if metadata_links has an entry for this abs_id → skip if yes (already linked)
  2. Search books table for matching title + author (normalised match via junction tables)
  3. If no book found → create book, authors, series via junction tables
  4. Create metadata_link (abs_id → book_id) with ON CONFLICT DO UPDATE
  5. For each format in item.formats → create in_library request if none exists for that type
  6. Commit after each item (avoid long locks)
```

### Author splitting

`_split_authors(author_string)` splits on: `,`, `&`, `;`, `\s+and\s+`

It also filters out `"- translator"` annotations (some sources append these).

Example: `"Brandon Sanderson, Janci Patterson"` → `["Brandon Sanderson", "Janci Patterson"]`

Authors are stored with `author_position` (1-based) to preserve order.

### Upsert pattern for authors/series

```python
# Get or create author
cursor = await db.execute("SELECT id FROM authors WHERE name = ?", (name,))
row = await cursor.fetchone()
if row:
    return row["id"]
# else INSERT and return new id
```

Series works the same way. Both use `name` as the uniqueness key.

### metadata_links table

This is the join table between our internal `books` and the external systems:

```sql
CREATE TABLE metadata_links (
    id TEXT PRIMARY KEY,
    book_id TEXT UNIQUE NOT NULL REFERENCES books(id),
    abs_id TEXT,           -- AudiobookShelf item ID
    hardcover_id TEXT,     -- Hardcover book ID (numeric, stored as string)
    linked_at TEXT NOT NULL
);
```

`UNIQUE` on `book_id` — one link per book. Use `ON CONFLICT(book_id) DO UPDATE` when upserting so that syncing ABS doesn't wipe a previously linked Hardcover ID.

Hardcover ID is populated lazily (when user views book detail and an enrichment happens, or when the user manually links via the metadata_links endpoint).

---

## 4. qBittorrent Download Handling

### Auth

qBittorrent uses cookie-based session auth. Login via `POST /api/v2/auth/login` with form data `{username, password}`. On success, response sets `SID` cookie. Cache this cookie globally and reuse it. On `403` response, re-authenticate and retry.

### Adding a torrent

`POST /api/v2/torrents/add` with form data `{urls: <magnet_or_url>, savepath: <path>, category: "bookorganize"}`

qBittorrent doesn't return the torrent hash synchronously. Two strategies for getting the hash:

1. **Magnet link**: parse `btih:([a-fA-F0-9]{40})` from the URI. Then poll `GET /api/v2/torrents/info?hashes={hash}` every 500ms (up to 10s) until the torrent appears.

2. **`.torrent` file URL**: download the file, extract the bencoded `info` dict, SHA1-hash it. This requires a minimal bencode parser (just enough to extract the `info` key). Then poll the same way.

If the hash is never confirmed after 20 polls (10 seconds), raise an error.

### Checking status

`GET /api/v2/torrents/info?hashes={hash}` returns an array. If empty, the torrent is unknown.

qBittorrent state strings map to normalised states:

| qBit states | Normalised |
|---|---|
| `uploading`, `stalledUP`, `forcedUP`, `pausedUP`, `queuedUP` | `completed` |
| `downloading`, `stalledDL`, `forcedDL`, `metaDL` | `downloading` |
| `pausedDL`, `queuedDL` | `paused` |
| `error`, `missingFiles` | `failed` |

### Save path for organisation

When completed, use `content_path` (preferred) or `save_path + "/" + name` as the path passed to the organiser. `content_path` is the direct path to the file/folder that was downloaded.

### File operation: copy vs move

For qBittorrent (torrents): **copy** files to the output directory, leave originals intact for seeding.

For SABnzbd (usenet): **move** files — no seeding, safe to move.

```python
use_copy = (download_client == "qbittorrent")
if use_copy:
    shutil.copy2(src, dest)
else:
    shutil.move(src, dest)
```

---

## 5. File Organisation and metadata.json

### Download monitor (background loop)

A background task polls every 15 seconds:

```python
SELECT d.*, r.status
FROM downloads d JOIN requests r ON d.request_id = r.id
WHERE d.status IN ('snatched', 'downloading')
AND d.download_client IS NOT NULL
```

For each active download, call `downloader.check(client, download_id)` to get normalised status, then:

- `downloading` (was `snatched`) → update both records to `downloading`
- `completed` → update download to `completed`, request to `downloaded`, then **fire auto-organize as asyncio task**
- `failed` → update download to `failed`, request back to `monitored` (so it can be retried)

### Organisation pipeline

```
organizer.organize(download_path, book_type, title, author, download_client, metadata)
```

1. Build target directory: `{output_dir}/[{type_prefix}/]{author}/{title}/`
   - `separate_type_dirs` setting controls whether the type prefix is added
   - Type prefix is configurable (`audiobook_prefix`, `ebook_prefix`)
   - All path components are sanitised (strip `<>:"/\\|?*`, leading/trailing dots/spaces)

2. **Multi-file audiobook detection**: if `download_path` is a directory with ≥2 audio files → merge to M4B (see below). Otherwise copy/move individual files.

3. **Single file**: rename to `{Title} - {Author}{ext}` when there's exactly one file. If multiple files (e.g. multi-part with no merge needed), keep original filenames.

4. **Dedup on dest**: if the target filename already exists, append ` (1)`, ` (2)`, etc.

5. Write `metadata.json` to the target directory.

### M4B merge

Uses `ffmpeg` (must be in PATH / installed in container).

```
Step 1: ffprobe each audio file → get duration and bitrate
Step 2: Write concat list file (ffmpeg concat demuxer format)
Step 3: Write FFMETADATA1 chapter file
         - Chapters derived from filenames (strip numeric prefixes, keep the descriptive part)
         - Cumulative timestamps in milliseconds
Step 4: Run ffmpeg:
         - If all inputs are .m4a or .m4b: -c copy (fast, no re-encode)
         - Otherwise: -c:a aac -b:a {avg_bitrate}k
         - Always -map_metadata 1 to embed chapters
Step 5: Move output .m4b to target_dir
Step 6: Clean up temp directory
```

Files are natural-sorted before merging (handles `Part01`, `Part2`, `Part10` correctly).

### metadata.json format (ABS-compatible)

Written to `{target_dir}/metadata.json`. ABS reads this on library scan and applies it to the item.

```json
{
  "title": "...",
  "subtitle": "...",
  "authors": ["Author One", "Author Two"],
  "narrators": ["Narrator Name"],
  "series": ["Series Name #3"],
  "genres": ["Science Fiction", "Space Opera"],
  "publishedYear": "2003",
  "publisher": "Baen Books",
  "description": "...",
  "isbn": "9781234567890",
  "asin": "B00XXXXX",
  "language": "English"
}
```

Key formatting rules:
- `authors` is an array (split on comma from the aggregated author string)
- `narrators` is an array
- `series` is an array of strings in format `"Series Name #Position"` — include `#position` only if a position is known
- `publishedYear` is a string, not an integer
- Only include keys for which there is a non-empty value

### Promote to in_library (post-organisation)

After organisation completes successfully:

1. Trigger `POST /api/libraries/{lib_id}/scan` on ABS
2. Wait 5 seconds (ABS scan is async)
3. Call `check_library(title, author)` on ABS
4. Find an item whose `formats` array contains an entry with `type == book_type`
5. If found:
   - Update `metadata_links` with the `abs_id` (using `ON CONFLICT DO UPDATE`)
   - Update request to `status='in_library'`, store `abs_id` and `abs_url`

If ABS scan fails or item not found: log a warning, leave request as `completed` — it can be synced later via the manual sync-library endpoint.

---

## 6. Request State Machine

```
requested → monitored → snatched → downloading → downloaded
                                                       ↓
                                                  organizing
                                                       ↓
                                                  completed → in_library
                                                       ↓
failed ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ↓
  ↓
downloaded (retry)
```

All transitions have an `updated_at` timestamp. Valid transitions:

```python
VALID_TRANSITIONS = {
    "requested":  ("monitored", "snatched", "cancelled"),
    "monitored":  ("requested", "snatched", "cancelled"),
    "snatched":   ("downloading", "cancelled"),
    "downloading":("downloaded", "cancelled"),
    "downloaded": ("organizing", "completed", "cancelled"),
    "organizing": ("completed", "failed", "cancelled"),
    "completed":  ("in_library", "cancelled"),
    "failed":     ("downloaded", "cancelled"),
}
```

**Deletion**: hard-delete rows (`DELETE FROM requests WHERE id = ?`). Do **not** use a `cancelled` status for deleted requests — this interferes with duplicate prevention. The `cancelled` status in `VALID_TRANSITIONS` is only for explicit user cancellation of in-progress requests (not deletion).

**Duplicate check on creation**: query for `book_id + type + narrator` where `status NOT IN ('cancelled')`. If any row found, return 409.

---

## 7. Prowlarr Search

`GET /api/v1/indexer` (with `X-Api-Key` header) returns all indexers; filter to `enable: true` to show available engines.

`GET /api/v1/search?query={q}&type=search&limit=50` returns torrent/NZB results.

Each result has:
- `protocol`: `"torrent"` or `"usenet"`
- `downloadUrl`: URL to pass to the download client
- `guid`: unique identifier from the indexer
- `title`: release name
- `indexer`: indexer name
- `size`: file size in bytes
- `infoUrl`: link to the release page

When sending a result to the download client:
- `torrent` → qBittorrent (`add_torrent(downloadUrl, save_path)`)
- `usenet` → SABnzbd (`add_nzb(downloadUrl)`)

---

## 8. Key Gotchas from BookOrganizeClaude

1. **SQLite GROUP_CONCAT**: `GROUP_CONCAT(DISTINCT col, ', ')` is not valid in SQLite (DISTINCT aggregates must have exactly one argument). Use `GROUP_CONCAT(col, ', ')` without DISTINCT.

2. **Normalized schema**: The `books` table has no `author`, `series`, or `series_id` columns. Always JOIN through `book_authors`/`book_series`. Forgetting this causes silent KeyErrors at runtime.

3. **Series endpoint returns wrong editions**: `series_by_pk` returns unpopular editions. For "missing books", get position list from series endpoint but metadata from `search(title)`.

4. **ABS formats array**: Items have a `formats` array, not a single `type` field. Iterate `formats` and check `fmt["type"]`. Never check `item.get("type")`.

5. **Cache buster**: Bump the `?v=N` query string on the `<script src="/app.js">` tag every time `app.js` changes, or browsers will serve stale JS.

6. **Docker rebuild**: `docker compose up -d --build` — the `--build` flag is required after any code change.

7. **No navigation after request submit**: After submitting a request from search results, do not navigate away. Update the card in-place with the new request status. Users want to request multiple books in a row.

8. **Deletion confirmation**: Use inline two-click confirmation (first click changes button to orange "Confirm?" state, second click executes). Do not use `window.confirm()` or `:contains()` CSS selectors (jQuery syntax, invalid in plain CSS).
