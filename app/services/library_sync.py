import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from rapidfuzz import fuzz

from ..database import get_db
from ..settings import get_settings

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_pos(pos) -> str | None:
    if not pos:
        return pos
    try:
        n = float(pos)
        return str(int(n)) if n == int(n) else str(n)
    except (ValueError, TypeError):
        return str(pos)


def _norm_title(s: str) -> str:
    """Normalise a title for fuzzy comparison."""
    s = re.sub(r'[\u200b-\u200f\u00ad\ufeff]', '', s)  # strip zero-width / soft-hyphen / BOM chars
    s = re.sub(r'\s*\([^)]*\)', '', s)    # strip parentheticals e.g. "(Third Edition)"
    s = re.sub(r'\s*&\s*', ' and ', s)    # & → and
    s = re.sub(r'[-]', ' ', s)             # hyphens → spaces
    s = re.sub(r'\s+', ' ', s).lower().strip()
    s = re.sub(r'^(the|a|an)\s+', '', s)  # strip leading article
    s = re.sub(r'\s+(a novel|a memoir|a thriller|a story|a tale)$', '', s)  # strip trailing marketing suffix
    return s


def _title_score(local: str, hc: str) -> int:
    """Score two titles across all combinations of full/subtitle-stripped forms."""
    local_short = local.split(':')[0].strip() if ':' in local else local
    hc_short = hc.split(':')[0].strip() if ':' in hc else hc
    return max(
        fuzz.token_sort_ratio(_norm_title(local),       _norm_title(hc)),
        fuzz.token_sort_ratio(_norm_title(local_short), _norm_title(hc_short)),
        fuzz.token_sort_ratio(_norm_title(local),       _norm_title(hc_short)),
        fuzz.token_sort_ratio(_norm_title(local_short), _norm_title(hc)),
    )


def _author_score(a: str, b: str) -> int:
    """Compare two author name strings, robust to period/space differences in initials."""
    def norm(s: str) -> str:
        return re.sub(r'[\s.]', '', s).lower()
    return max(
        fuzz.token_sort_ratio(a.lower(), b.lower()),
        fuzz.ratio(norm(a), norm(b)),
        fuzz.token_set_ratio(a.lower(), b.lower()),
    )


def _split_authors(author_string: str) -> list[str]:
    """Split a combined author string into individual author names."""
    if not author_string:
        return []
    lower = author_string.lower()
    parts = re.split(r",\s+|\s+&\s+|\s+and\s+|;\s*", lower)
    result = []
    pos = 0
    for part in parts:
        part = part.strip()
        # Strip translator/editor annotations like "(translator)"
        part = re.sub(r"\s*\([^)]*\)\s*$", "", part).strip()
        if not part:
            continue
        idx = author_string.lower().find(part, pos)
        if idx >= 0:
            result.append(author_string[idx: idx + len(part)])
            pos = idx + len(part)
        else:
            result.append(part.title())
    return [r for r in result if r]


async def _set_hc_author_id(db, author_id: str, hc_author_id: str, hc_author_slug: str = "") -> bool:
    """Set hardcover_author_id (and slug) on author_links, skipping if already claimed. Returns True if set."""
    conflict = await (
        await db.execute(
            "SELECT author_id FROM author_links WHERE hardcover_author_id = ?", (hc_author_id,)
        )
    ).fetchone()
    if conflict and conflict[0] != author_id:
        logger.warning(f"HC author {hc_author_id} already linked to {conflict[0]}, skipping {author_id}")
        return False
    await db.execute(
        "UPDATE author_links SET hardcover_author_id = ?, hardcover_author_slug = ? WHERE author_id = ? AND (hardcover_author_id IS NULL OR hardcover_author_id = '')",
        (hc_author_id, hc_author_slug or None, author_id),
    )
    return True


async def _set_hc_series_id(db, series_id: str, hc_series_id: str, hc_series_slug: str = "") -> bool:
    """Set hardcover_series_id (and slug) on series_links, skipping if already claimed. Returns True if set."""
    conflict = await (
        await db.execute(
            "SELECT series_id FROM series_links WHERE hardcover_series_id = ?", (hc_series_id,)
        )
    ).fetchone()
    if conflict and conflict[0] != series_id:
        logger.warning(f"HC series {hc_series_id} already linked to {conflict[0]}, skipping {series_id}")
        return False
    await db.execute(
        "UPDATE series_links SET hardcover_series_id = ?, hardcover_series_slug = ? WHERE series_id = ? AND (hardcover_series_id IS NULL OR hardcover_series_id = '')",
        (hc_series_id, hc_series_slug or None, series_id),
    )
    return True


async def _get_or_create_author(db, name: str, abs_author_id: str = "") -> str:
    """Return author_id, creating author and author_links rows if needed."""
    name = " ".join(name.split())  # collapse internal whitespace
    row = await (
        await db.execute("SELECT id FROM authors WHERE lower(name) = lower(?)", (name,))
    ).fetchone()
    if row:
        author_id = row[0]
    else:
        author_id = str(uuid.uuid4())
        now = _now()
        await db.execute(
            "INSERT INTO authors (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (author_id, name, now, now),
        )
    await db.execute(
        "INSERT OR IGNORE INTO author_links (id, author_id, linked_at) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), author_id, _now()),
    )
    if abs_author_id:
        await db.execute(
            "UPDATE author_links SET abs_author_id = ? WHERE author_id = ? AND (abs_author_id IS NULL OR abs_author_id = '')",
            (abs_author_id, author_id),
        )
    return author_id


async def _get_or_create_series(db, name: str, abs_series_id: str = "", hc_series_id: str = "") -> str:
    """Return series_id, creating series and series_links rows if needed.

    Lookup order: HC series ID → exact name → create new.
    """
    name = " ".join(name.split())  # collapse internal whitespace

    # 1. Match by HC series ID — most authoritative, avoids name-variant duplicates
    if hc_series_id:
        row = await (
            await db.execute(
                "SELECT series_id FROM series_links WHERE hardcover_series_id = ?", (hc_series_id,)
            )
        ).fetchone()
        if row:
            series_id = row[0]
            if abs_series_id:
                await db.execute(
                    "UPDATE series_links SET abs_series_id = ? WHERE series_id = ? AND (abs_series_id IS NULL OR abs_series_id = '')",
                    (abs_series_id, series_id),
                )
            return series_id

    # 2. Match by ABS series ID — handles ABS name variants that differ from our stored name
    if abs_series_id:
        row = await (
            await db.execute(
                "SELECT series_id FROM series_links WHERE abs_series_id = ?", (abs_series_id,)
            )
        ).fetchone()
        if row:
            return row[0]

    # 3. Match by name
    row = await (
        await db.execute("SELECT id FROM series WHERE lower(name) = lower(?)", (name,))
    ).fetchone()
    if row:
        series_id = row[0]
    else:
        series_id = str(uuid.uuid4())
        now = _now()
        await db.execute(
            "INSERT INTO series (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (series_id, name, now, now),
        )
    await db.execute(
        "INSERT OR IGNORE INTO series_links (id, series_id, linked_at) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), series_id, _now()),
    )
    if abs_series_id:
        await db.execute(
            "UPDATE series_links SET abs_series_id = ? WHERE series_id = ? AND (abs_series_id IS NULL OR abs_series_id = '')",
            (abs_series_id, series_id),
        )
    return series_id


async def _hc_book_search(title: str, api_key: str, author: str = "", pages: int = 3) -> list:
    """Fetch HC book search results for both title-only and title+author queries concurrently.

    HC caps per_page at 25, so we fan out across pages and queries and merge.
    Returns deduplicated hits; order is preserved (title+author hits come first so
    the scorer sees them, but final ordering is left to the caller).
    """
    gql = 'query Search($q: String!, $page: Int!) { search(query: $q, query_type: "Book", per_page: 25, page: $page) { results } }'
    headers = {"Authorization": f"Bearer {api_key}"}

    # Title-only: paginate broadly. Title+author: single page — it's targeted enough.
    fetches: list[tuple[str, int]] = [(title.strip(), p) for p in range(1, pages + 1)]
    if author.strip():
        fetches.append((f"{title.strip()} {author.strip()}", 1))

    async def fetch_page(client: httpx.AsyncClient, query: str, page: int) -> list:
        resp = await client.post(
            "https://api.hardcover.app/v1/graphql",
            json={"query": gql, "variables": {"q": query, "page": page}},
            headers=headers,
        )
        if resp.status_code == 429:
            resp.raise_for_status()
        resp.raise_for_status()
        return resp.json()["data"]["search"]["results"].get("hits", [])

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(
            *[fetch_page(client, q, p) for q, p in fetches],
            return_exceptions=True,
        )

    seen: set = set()
    deduped: list = []
    for r in results:
        if not isinstance(r, list):
            continue
        for h in r:
            doc_id = h.get("document", {}).get("id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                deduped.append(h)

    # Tiebreaker: more popular books should win equal-score matches
    return sorted(deduped, key=lambda h: h.get("document", {}).get("users_count") or 0, reverse=True)


async def _fetch_hc_book_meta(hc_book_id: int, api_key: str) -> dict:
    """Fetch slug, release_date, and canonical_id for a single HC book.
    If the book has a canonical_id, follows it once and returns the canonical book's
    data with 'canonical_id' set so callers can update stored HC IDs."""
    gql = "query Meta($id: Int!) { books_by_pk(id: $id) { slug release_date canonical_id } }"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": gql, "variables": {"id": hc_book_id}},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            resp.raise_for_status()
        book = (resp.json().get("data") or {}).get("books_by_pk") or {}
    except Exception as e:
        logger.warning("_fetch_hc_book_meta(%s) failed: %s", hc_book_id, e)
        return {}
    canonical_id = book.get("canonical_id")
    if canonical_id:
        canon = await _fetch_hc_book_meta(int(canonical_id), api_key)
        if canon:
            canon["canonical_id"] = str(canonical_id)
        return canon
    return {"slug": book.get("slug") or "", "release_date": book.get("release_date") or ""}


async def _fetch_hc_release_date(hc_book_id: int, api_key: str) -> str:
    """Fetch release_date for a single HC book. Returns ISO date string or ''."""
    gql = "query ReleaseDate($id: Int!) { books_by_pk(id: $id) { release_date } }"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": gql, "variables": {"id": hc_book_id}},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
        book = (resp.json().get("data") or {}).get("books_by_pk") or {}
        return book.get("release_date") or ""
    except Exception as e:
        logger.warning("_fetch_hc_release_date(%s) failed: %s", hc_book_id, e)
        return ""


async def _hc_series_for_book(hc_book_id: str, api_key: str) -> list:
    """Return HC series that a given HC book belongs to (list of dicts with id/name/slug/books_count)."""
    gql = """
    query BookSeries($id: Int!) {
      books_by_pk(id: $id) {
        book_series {
          series {
            id
            name
            slug
            books_count
          }
        }
      }
    }
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": gql, "variables": {"id": int(hc_book_id)}},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
        book = resp.json().get("data", {}).get("books_by_pk") or {}
        return [
            entry["series"]
            for entry in (book.get("book_series") or [])
            if entry.get("series") and (entry["series"].get("books_count") or 0) > 0
        ]
    except Exception as e:
        logger.debug(f"HC series lookup for book {hc_book_id} failed: {e}")
        return []


async def _link_to_hardcover(book_id: str, settings: dict) -> bool:
    """Attempt to link a book to Hardcover. Returns True if a match was found."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return False

    async with get_db() as db:
        book_row = await (
            await db.execute("SELECT title FROM books WHERE id = ?", (book_id,))
        ).fetchone()
        if not book_row:
            return False
        title = book_row[0]

        author_rows = await (
            await db.execute(
                """SELECT a.id, a.name FROM authors a
                   JOIN book_authors ba ON ba.author_id = a.id
                   WHERE ba.book_id = ?
                   ORDER BY ba.author_position""",
                (book_id,),
            )
        ).fetchall()
        author = author_rows[0]["name"] if author_rows else ""

        book_series_rows = await (
            await db.execute(
                """SELECT bs.series_id, s.name, sl.hardcover_series_id
                   FROM book_series bs
                   JOIN series s ON s.id = bs.series_id
                   LEFT JOIN series_links sl ON sl.series_id = bs.series_id
                   WHERE bs.book_id = ?""",
                (book_id,),
            )
        ).fetchall()
        known_hc_series_ids = {
            str(r["hardcover_series_id"])
            for r in book_series_rows
            if r["hardcover_series_id"]
        }

    if not title.strip():
        return False

    try:
        hits = await _hc_book_search(title, api_key, author=author)
    except httpx.HTTPStatusError:
        raise
    except Exception as e:
        logger.warning(f"HC link search failed for book {book_id}: {e}")
        return False

    if not hits:
        logger.debug(f"HC no results for '{title}' by '{author}'")
        return False

    best = None
    best_score = (0, 0, 0)
    for hit in hits:
        doc = hit.get("document", {})
        doc_title = doc.get("title", "") or ""
        contributors = doc.get("contributions") or doc.get("cached_contributors") or []
        doc_authors = [
            c.get("author_name") or (c.get("author") or {}).get("name", "") or ""
            for c in contributors if isinstance(c, dict)
        ]
        doc_authors = [n for n in doc_authors if n]
        doc_author = doc_authors[0] if doc_authors else ""

        t_score = _title_score(title, doc_title)
        local_author_names = [r["name"] for r in author_rows if r["name"]]
        if local_author_names and doc_authors:
            a_score = max(
                _author_score(la, da)
                for la in local_author_names
                for da in doc_authors
            )
        else:
            a_score = 85

        featured = doc.get("featured_series") or {}
        doc_series_id = str((featured.get("series") or {}).get("id") or "")
        has_any_series = bool(featured or doc.get("series_names"))
        if known_hc_series_ids and doc_series_id in known_hc_series_ids:
            series_bonus = 2
        elif has_any_series:
            series_bonus = 1
        else:
            series_bonus = 0

        logger.debug(f"HC candidate '{doc_title}' by '{doc_author}': t={t_score} a={a_score} s={series_bonus}")

        if t_score >= 90 and a_score >= 85 and (t_score, a_score, series_bonus) > best_score:
            best = doc
            best_score = (t_score, a_score, series_bonus)

    if not best:
        logger.warning(f"HC no confident match for '{title}' by '{author}' (best scores: {best_score})")
        return False

    hardcover_id = str(best.get("id", ""))
    hardcover_slug = best.get("slug", "")
    if not hardcover_id:
        return False

    # Fetch exact release_date and canonical ID from HC GraphQL
    meta = await _fetch_hc_book_meta(int(hardcover_id), api_key)
    release_date = meta.get("release_date") or ""
    if meta.get("canonical_id"):
        hardcover_id = meta["canonical_id"]
        hardcover_slug = meta.get("slug") or hardcover_slug

    # Extract series from featured_series and series_names (confirmed present in HC Typesense docs)
    featured = best.get("featured_series") or {}
    featured_series_name = ((featured.get("series") or {}).get("name") or "").strip()
    featured_series_id = str((featured.get("series") or {}).get("id") or "")
    series_names = best.get("series_names") or []

    # Build list of HC contributors: [{hc_author_id, name}]
    hc_contributors = []
    for c in (best.get("contributions") or best.get("cached_contributors") or []):
        if not isinstance(c, dict):
            continue
        hc_author_id = str(
            c.get("author_id")
            or (c.get("author") or {}).get("id", "")
            or ""
        )
        hc_author_name = (
            c.get("author_name")
            or (c.get("author") or {}).get("name", "")
            or ""
        )
        if hc_author_id and hc_author_name:
            hc_contributors.append({"id": hc_author_id, "name": hc_author_name})

    async with get_db() as db:
        existing = await (
            await db.execute(
                "SELECT book_id FROM book_links WHERE hardcover_id = ?", (hardcover_id,)
            )
        ).fetchone()
        if existing and existing[0] != book_id:
            logger.warning(
                f"HC book {hardcover_id} already linked to book {existing[0]}, skipping {book_id}"
            )
            return False
        await db.execute(
            "UPDATE book_links SET hardcover_id = ?, hardcover_slug = ? WHERE book_id = ?",
            (hardcover_id, hardcover_slug, book_id),
        )
        if release_date:
            await db.execute(
                "UPDATE books SET release_date = ?, release_date_fetched = 1 WHERE id = ?",
                (release_date, book_id),
            )
        else:
            await db.execute(
                "UPDATE books SET release_date_fetched = 1 WHERE id = ?",
                (book_id,),
            )
        for row in book_series_rows:
            local_series_id, local_series_name = row["series_id"], row["name"]
            best_match_name = None
            best_s_score = 0
            for sname in series_names:
                score = fuzz.token_sort_ratio(local_series_name.lower(), sname.lower())
                if score >= 80 and score > best_s_score:
                    best_match_name = sname
                    best_s_score = score
            if best_match_name and featured_series_id and featured_series_name:
                if fuzz.token_sort_ratio(best_match_name.lower(), featured_series_name.lower()) >= 80:
                    await _set_hc_series_id(db, local_series_id, featured_series_id)
        for local_author in author_rows:
            local_id = local_author["id"]
            local_name = local_author["name"]
            best_hc_author = None
            best_a_score = 0
            for hc in hc_contributors:
                score = _author_score(local_name, hc["name"])
                if score >= 85 and score > best_a_score:
                    best_hc_author = hc
                    best_a_score = score
            if best_hc_author:
                await _set_hc_author_id(db, local_id, best_hc_author["id"])
        await db.commit()

    return True


async def _upsert_task_state(task: str, running: bool, last_result: str = None):
    async with get_db() as db:
        if running:
            if last_result is not None:
                await db.execute(
                    """INSERT INTO task_state (task, running, last_result) VALUES (?, 1, ?)
                       ON CONFLICT(task) DO UPDATE SET running = 1, last_result = ?""",
                    (task, last_result, last_result),
                )
            else:
                await db.execute(
                    """INSERT INTO task_state (task, running) VALUES (?, 1)
                       ON CONFLICT(task) DO UPDATE SET running = 1""",
                    (task,),
                )
        else:
            now = _now()
            await db.execute(
                """INSERT INTO task_state (task, running, last_run, last_result) VALUES (?, 0, ?, ?)
                   ON CONFLICT(task) DO UPDATE SET running = 0, last_run = ?, last_result = ?""",
                (task, now, last_result, now, last_result),
            )
        await db.commit()


async def _hc_rate_limited_loop(
    items: list, fn, deadline: float, on_progress=None, progress_interval: float = 4.0
) -> dict:
    """Run fn(item) for each item, retrying 429s up to MAX_RETRIES times.

    on_progress(linked, failed, remaining) is called roughly every progress_interval seconds.
    """
    MAX_RETRIES = 5
    counters = {"linked": 0, "failed": 0, "skipped": 0}
    queue = [[item, 0] for item in items]  # [item, retry_count]
    backoff = 0.0
    last_progress = time.monotonic() - progress_interval  # fire immediately on first item
    while queue:
        if time.monotonic() >= deadline:
            counters["skipped"] += len(queue)
            break
        item, retries = queue.pop(0)
        await asyncio.sleep(backoff if backoff else 1.0)
        try:
            if await fn(item):
                counters["linked"] += 1
                backoff = 0.0
            else:
                counters["failed"] += 1
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                backoff = min((backoff or 2.0) * 2, 60.0)
                if retries < MAX_RETRIES:
                    queue.append([item, retries + 1])
                    logger.warning(f"HC rate limited, backing off {backoff:.0f}s (retry {retries+1}/{MAX_RETRIES})")
                else:
                    logger.warning(f"HC rate limited, max retries exceeded for item")
                    counters["failed"] += 1
            else:
                logger.warning(f"HC HTTP error: {e}")
                backoff = 0.0
                counters["failed"] += 1

        now = time.monotonic()
        if on_progress and (now - last_progress) >= progress_interval:
            await on_progress(counters["linked"], counters["failed"], len(queue))
            last_progress = now

    if on_progress:
        await on_progress(counters["linked"], counters["failed"], 0)
    return counters


async def _hc_link_books(settings: dict, deadline: float, on_progress=None) -> dict:
    """Link books with no hardcover_id. Primary path — also sets author/series HC IDs from result."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"linked": 0, "failed": 0, "skipped": 0}
    async with get_db() as db:
        rows = await (
            await db.execute(
                "SELECT bl.book_id FROM book_links bl WHERE bl.hardcover_id IS NULL OR bl.hardcover_id = '' ORDER BY bl.linked_at"
            )
        ).fetchall()
    book_ids = [r[0] for r in rows]
    return await _hc_rate_limited_loop(
        book_ids, lambda bid: _link_to_hardcover(bid, settings), deadline, on_progress=on_progress
    )


async def _hc_catchup_authors(settings: dict, deadline: float, on_progress=None) -> dict:
    """Catch-up pass: link authors with no hardcover_author_id via HC author search."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"linked": 0, "failed": 0, "skipped": 0}

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT al.author_id, a.name, al.hardcover_author_id FROM author_links al
                   JOIN authors a ON a.id = al.author_id
                   WHERE al.hardcover_author_id IS NULL OR al.hardcover_author_id = ''
                      OR al.hardcover_author_slug IS NULL OR al.hardcover_author_slug = ''
                   ORDER BY al.linked_at"""
            )
        ).fetchall()

    async def link_author(row) -> bool:
        author_id, name, existing_hc_id = row["author_id"], row["name"], row["hardcover_author_id"]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.hardcover.app/v1/graphql",
                    json={
                        "query": 'query Search($q: String!) { search(query: $q, query_type: "author", per_page: 15) { results } }',
                        "variables": {"q": name},
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 429:
                    resp.raise_for_status()
                resp.raise_for_status()
                hits = resp.json()["data"]["search"]["results"].get("hits", [])
        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.warning(f"HC author search failed for '{name}': {e}")
            return False

        if existing_hc_id:
            # Already linked — find the result matching the known HC ID and extract its slug
            slug = ""
            for hit in hits:
                doc = hit.get("document", {})
                if str(doc.get("id", "")) == str(existing_hc_id):
                    slug = doc.get("slug", "") or ""
                    break
            if not slug:
                logger.debug(f"HC author {existing_hc_id} not in search results for '{name}', can't backfill slug")
                return False
            async with get_db() as db:
                await db.execute(
                    "UPDATE author_links SET hardcover_author_slug = ? WHERE author_id = ?",
                    (slug, author_id),
                )
                await db.commit()
            return True

        best, best_score = None, 0
        for hit in hits:
            doc = hit.get("document", {})
            score = _author_score(name, doc.get("name") or "")
            if score >= 85 and score > best_score:
                best, best_score = doc, score

        if not best:
            logger.debug(f"HC no author match for '{name}'")
            return False

        hc_author_id = str(best.get("id", ""))
        hc_author_slug = best.get("slug", "") or ""
        if not hc_author_id:
            return False

        async with get_db() as db:
            linked = await _set_hc_author_id(db, author_id, hc_author_id, hc_author_slug)
            await db.commit()
        return linked

    return await _hc_rate_limited_loop(list(rows), link_author, deadline, on_progress=on_progress)


async def _hc_catchup_series(settings: dict, deadline: float, on_progress=None) -> dict:
    """Catch-up pass: link series with no hardcover_series_id via HC series search."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"linked": 0, "failed": 0, "skipped": 0}

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT sl.series_id, s.name, sl.hardcover_series_id FROM series_links sl
                   JOIN series s ON s.id = sl.series_id
                   WHERE sl.hardcover_series_id IS NULL OR sl.hardcover_series_id = ''
                      OR sl.hardcover_series_slug IS NULL OR sl.hardcover_series_slug = ''
                   ORDER BY sl.linked_at"""
            )
        ).fetchall()

    async def link_series(row) -> bool:
        series_id, name, existing_hc_id = row["series_id"], row["name"], row["hardcover_series_id"]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.hardcover.app/v1/graphql",
                    json={
                        "query": 'query Search($q: String!) { search(query: $q, query_type: "series", per_page: 15) { results } }',
                        "variables": {"q": name},
                    },
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 429:
                    resp.raise_for_status()
                resp.raise_for_status()
                hits = resp.json()["data"]["search"]["results"].get("hits", [])
        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.warning(f"HC series search failed for '{name}': {e}")
            return False

        hits = [h for h in hits if (h.get("document", {}).get("books_count") or 0) > 0]
        hits = sorted(hits, key=lambda h: h.get("document", {}).get("books_count") or 0, reverse=True)

        if existing_hc_id:
            # Already linked — find the result matching the known HC ID and extract its slug
            slug = ""
            for hit in hits:
                doc = hit.get("document", {})
                if str(doc.get("id", "")) == str(existing_hc_id):
                    slug = doc.get("slug", "") or ""
                    break
            if not slug:
                logger.debug(f"HC series {existing_hc_id} not in search results for '{name}', can't backfill slug")
                return False
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_links SET hardcover_series_slug = ? WHERE series_id = ?",
                    (slug, series_id),
                )
                await db.commit()
            return True

        best, best_score = None, 0
        for hit in hits:
            doc = hit.get("document", {})
            score = fuzz.token_sort_ratio(_norm_title(name), _norm_title(doc.get("name") or ""))
            if score >= 85 and score > best_score:
                best, best_score = doc, score

        if not best:
            logger.debug(f"HC no series match for '{name}'")
            return False

        hc_series_id = str(best.get("id", ""))
        hc_series_slug = best.get("slug", "") or ""
        if not hc_series_id:
            return False

        async with get_db() as db:
            set_ok = await _set_hc_series_id(db, series_id, hc_series_id, hc_series_slug)
            await db.commit()
        return set_ok

    return await _hc_rate_limited_loop(list(rows), link_series, deadline, on_progress=on_progress)


async def _hc_refresh_meta(api_key: str) -> int:
    """Fetch and store slug + release_date for HC-linked books missing either, or with a future date. Returns count updated."""
    if not api_key:
        return 0
    today = datetime.now(timezone.utc).date().isoformat()
    async with get_db() as db:
        stale_rows = await (
            await db.execute(
                """SELECT b.id, bl.hardcover_id FROM books b
                   JOIN book_links bl ON bl.book_id = b.id
                   WHERE bl.hardcover_id IS NOT NULL AND bl.hardcover_id != ''
                     AND (
                       (b.release_date_fetched = 0 AND (b.release_date IS NULL OR b.release_date = ''))
                       OR b.release_date >= ?
                       OR bl.hardcover_slug IS NULL OR bl.hardcover_slug = ''
                     )""",
                (today,),
            )
        ).fetchall()
    if not stale_rows:
        return 0
    sem = asyncio.Semaphore(2)
    updated = 0

    async def _refresh_one(book_id: str, hc_id: str) -> None:
        nonlocal updated
        async with sem:
            await asyncio.sleep(0.3)
            meta = await _fetch_hc_book_meta(int(hc_id), api_key)
            if not meta:
                return
            async with get_db() as db:
                if meta.get("release_date"):
                    await db.execute(
                        "UPDATE books SET release_date = ?, release_date_fetched = 1 WHERE id = ?",
                        (meta["release_date"], book_id),
                    )
                else:
                    # HC confirmed no date — mark as fetched so auto-search knows to skip
                    await db.execute(
                        "UPDATE books SET release_date_fetched = 1 WHERE id = ?",
                        (book_id,),
                    )
                if meta.get("slug"):
                    await db.execute(
                        "UPDATE book_links SET hardcover_slug = ? WHERE book_id = ? AND (hardcover_slug IS NULL OR hardcover_slug = '')",
                        (meta["slug"], book_id),
                    )
                if meta.get("canonical_id"):
                    await db.execute(
                        "UPDATE book_links SET hardcover_id = ? WHERE book_id = ?",
                        (meta["canonical_id"], book_id),
                    )
                    logger.info("_refresh_one: corrected hardcover_id for %s to canonical %s", book_id, meta["canonical_id"])
                await db.commit()
            updated += 1

    await asyncio.gather(*[_refresh_one(r[0], r[1]) for r in stale_rows])
    return updated


def _is_primary_position(pos: str) -> bool:
    try:
        n = float(pos)
        return n == int(n)
    except (ValueError, TypeError):
        return False


def _book_is_unreleased(b: dict) -> bool:
    """True if the book has no date or its release date is in the future.

    No date (empty string) means HC has no release date for this book — treat as
    upcoming/unannounced. YYYY-01-01 for current or future year is year-precision
    only (no confirmed day), so also treat as upcoming.
    """
    from datetime import date
    rd = (b.get("release_date") or "")[:10]
    if not rd:
        return True
    try:
        d = date.fromisoformat(rd)
        today = date.today()
        if d.month == 1 and d.day == 1 and d.year >= today.year:
            return True
        return d > today
    except ValueError:
        return True


def _compute_series_stats(all_books: list, owned_hc_ids: set, show_secondary: bool) -> dict:
    """Compute missing/upcoming counts for a series, respecting show_secondary."""
    primary = [
        b for b in all_books
        if not b.get("compilation") and _is_primary_position(b.get("series_position") or "")
    ]
    all_works = [b for b in all_books if not b.get("compilation")]

    def _counts(subset):
        not_owned = [
            b for b in subset
            if b.get("metadata_id") not in owned_hc_ids
            and not any(aid in owned_hc_ids for aid in (b.get("alt_ids") or []))
        ]
        return (
            sum(1 for b in not_owned if not _book_is_unreleased(b)),
            sum(1 for b in not_owned if _book_is_unreleased(b)),
        )

    missing_primary, upcoming_primary = _counts(primary)
    missing_all, upcoming_all = _counts(all_works)

    return {
        "missing_primary": missing_primary,
        "upcoming_primary": upcoming_primary,
        "missing_all": missing_all,
        "upcoming_all": upcoming_all,
        "total_primary": len(primary),
        "total_all": len(all_works),
    }


async def _hc_refresh_series_cache(settings: dict, deadline: float) -> dict:
    """Pre-fetch full series book lists for all HC-linked series and cache them.

    Stores series_books_rich (full list for the detail page) and
    series_missing_stats (lightweight counts for the list page).
    Books data is skipped when still fresh; stats are always recomputed so
    they reflect the current library state.
    """
    from .book_search import get_hc_series_books

    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"updated": 0, "skipped": 0}

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    expires_iso = (now_dt + timedelta(days=14)).isoformat()

    async with get_db() as db:
        series_rows = await (
            await db.execute(
                """SELECT sl.series_id, sl.hardcover_series_id, s.show_secondary_works
                   FROM series_links sl
                   JOIN series s ON s.id = sl.series_id
                   WHERE sl.hardcover_series_id IS NOT NULL AND sl.hardcover_series_id != ''"""
            )
        ).fetchall()

    updated = 0
    skipped = 0

    for row in series_rows:
        if time.monotonic() > deadline:
            break

        hc_series_id = row["hardcover_series_id"]
        series_id = row["series_id"]
        show_secondary = bool(row["show_secondary_works"])

        try:
            # Check if books data is still fresh — reuse cached if so
            async with get_db() as db:
                cache_row = await (
                    await db.execute(
                        "SELECT results_json FROM metadata_cache WHERE query = ? AND source = ? AND expires_at > ?",
                        (hc_series_id, "series_books_rich", now_iso),
                    )
                ).fetchone()

            if cache_row:
                all_books = json.loads(cache_row["results_json"])
                skipped += 1
            else:
                all_books = await get_hc_series_books(hc_series_id, api_key)
                async with get_db() as db:
                    await db.execute(
                        """INSERT INTO metadata_cache (id, query, source, results_json, created_at, expires_at)
                           VALUES (?, ?, ?, ?, ?, ?)
                           ON CONFLICT(query, source) DO UPDATE SET
                             results_json = excluded.results_json,
                             created_at   = excluded.created_at,
                             expires_at   = excluded.expires_at""",
                        (str(uuid.uuid4()), hc_series_id, "series_books_rich",
                         json.dumps(all_books), now_iso, expires_iso),
                    )
                    await db.commit()

            # Always recompute stats — they depend on current library state
            async with get_db() as db:
                owned_rows = await (
                    await db.execute(
                        """SELECT bl.hardcover_id FROM book_series bs
                           JOIN books b ON b.id = bs.book_id
                           LEFT JOIN book_links bl ON bl.book_id = b.id
                           WHERE bs.series_id = ?
                           AND EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = b.id)""",
                        (series_id,),
                    )
                ).fetchall()
                owned_hc_ids = {r["hardcover_id"] for r in owned_rows if r["hardcover_id"]}

                # Cross-reference local release_date for books already in DB
                local_dates = await (
                    await db.execute(
                        """SELECT bl.hardcover_id, b.release_date
                           FROM book_series bs
                           JOIN books b ON b.id = bs.book_id
                           LEFT JOIN book_links bl ON bl.book_id = b.id
                           WHERE bs.series_id = ? AND b.release_date IS NOT NULL""",
                        (series_id,),
                    )
                ).fetchall()
                local_date_map = {r["hardcover_id"]: r["release_date"] for r in local_dates if r["hardcover_id"]}

                # Patch in local release dates where HC didn't provide them
                for b in all_books:
                    if not b.get("release_date") and b.get("metadata_id") in local_date_map:
                        b["release_date"] = local_date_map[b["metadata_id"]]

                stats = _compute_series_stats(all_books, owned_hc_ids, show_secondary)

                await db.execute(
                    """INSERT INTO metadata_cache (id, query, source, results_json, created_at, expires_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(query, source) DO UPDATE SET
                         results_json = excluded.results_json,
                         created_at   = excluded.created_at,
                         expires_at   = excluded.expires_at""",
                    (str(uuid.uuid4()), hc_series_id, "series_missing_stats",
                     json.dumps(stats), now_iso, expires_iso),
                )
                await db.commit()

            updated += 1
        except Exception as e:
            logger.warning("_hc_refresh_series_cache(%s): %s", hc_series_id, e)

        await asyncio.sleep(1)

    return {"updated": updated, "skipped": skipped}


async def cache_refresh() -> dict:
    """HC linking: books (primary), then author/series catch-up. Rate-limited, 1hr time slice."""
    settings = await get_settings()
    deadline = time.monotonic() + 3600

    # Snapshot of completed phases, built up as we go
    done: dict[str, dict] = {}

    def _fmt_progress(phase: str, linked: int, failed: int, remaining: int) -> str:
        parts = [f"{p}: {r['linked']} linked, {r['failed']} failed" for p, r in done.items()]
        parts.append(f"{phase}: {linked} linked, {failed} failed, {remaining} remaining")
        return " | ".join(parts)

    async def make_progress(phase: str):
        async def _cb(linked: int, failed: int, remaining: int):
            await _upsert_task_state(
                "cache_refresh", running=True,
                last_result=_fmt_progress(phase, linked, failed, remaining),
            )
        return _cb

    await _upsert_task_state("cache_refresh", running=True, last_result="starting...")
    try:
        b = await _hc_link_books(settings, deadline, on_progress=await make_progress("books"))
        done["books"] = b
        a = await _hc_catchup_authors(settings, deadline, on_progress=await make_progress("authors"))
        done["authors"] = a
        s = await _hc_catchup_series(settings, deadline, on_progress=await make_progress("series"))
        api_key = settings.get("hardcover", {}).get("api_key", "")
        meta_updated = await _hc_refresh_meta(api_key)
        sc = await _hc_refresh_series_cache(settings, deadline)
        result = (
            f"books {b['linked']}/{b['linked']+b['failed']} linked"
            + (f" ({b['skipped']} skipped)" if b['skipped'] else "")
            + f" | authors {a['linked']}/{a['linked']+a['failed']}"
            + f" | series {s['linked']}/{s['linked']+s['failed']}"
            + f" | meta {meta_updated} refreshed"
            + f" | series cache {sc['updated']} updated, {sc['skipped']} fresh"
        )
        logger.info(f"cache_refresh complete: {result}")
        await _upsert_task_state("cache_refresh", running=False, last_result=result)
        return {"books": b, "authors": a, "series": s, "meta_updated": meta_updated, "series_cache": sc}
    except Exception as e:
        logger.error(f"cache_refresh failed: {e}", exc_info=True)
        await _upsert_task_state("cache_refresh", running=False, last_result=f"error: {e}")
        raise


async def try_link_book(book_id: str, settings: dict) -> dict:
    """Run HC book match verbosely. Persists if a match is found. Returns full log."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"result": "no_api_key"}

    async with get_db() as db:
        book_row = await (
            await db.execute("SELECT title FROM books WHERE id = ?", (book_id,))
        ).fetchone()
        if not book_row:
            return {"result": "not_found"}
        title = book_row[0]

        author_rows = await (
            await db.execute(
                """SELECT a.id, a.name FROM authors a
                   JOIN book_authors ba ON ba.author_id = a.id
                   WHERE ba.book_id = ? ORDER BY ba.author_position""",
                (book_id,),
            )
        ).fetchall()
        author = author_rows[0]["name"] if author_rows else ""

        book_series_rows = await (
            await db.execute(
                """SELECT bs.series_id, s.name, sl.hardcover_series_id
                   FROM book_series bs
                   JOIN series s ON s.id = bs.series_id
                   LEFT JOIN series_links sl ON sl.series_id = bs.series_id
                   WHERE bs.book_id = ?""",
                (book_id,),
            )
        ).fetchall()
        known_hc_series_ids = {
            str(r["hardcover_series_id"])
            for r in book_series_rows
            if r["hardcover_series_id"]
        }

        existing_link = await (
            await db.execute(
                "SELECT hardcover_id FROM book_links WHERE book_id = ?", (book_id,)
            )
        ).fetchone()

    log: dict = {
        "title": title,
        "author": author,
        "already_linked": bool(existing_link and existing_link[0]),
        "current_hardcover_id": existing_link[0] if existing_link else None,
        "candidates": [],
        "result": None,
    }

    try:
        hits = await _hc_book_search(title, api_key, author=author)
    except Exception as e:
        log["result"] = "error"
        log["error"] = str(e)
        return log

    if not hits:
        log["result"] = "no_results"
        return log

    best = None
    best_score = (0, 0)
    for hit in hits:
        doc = hit.get("document", {})
        doc_title = doc.get("title", "") or ""
        contributors = doc.get("contributions") or doc.get("cached_contributors") or []
        doc_authors = [
            c.get("author_name") or (c.get("author") or {}).get("name", "") or ""
            for c in contributors if isinstance(c, dict)
        ]
        doc_authors = [n for n in doc_authors if n]
        doc_author = doc_authors[0] if doc_authors else ""
        t_score = _title_score(title, doc_title)
        local_author_names = [r["name"] for r in author_rows if r["name"]]
        if local_author_names and doc_authors:
            a_score = max(
                _author_score(la, da)
                for la in local_author_names
                for da in doc_authors
            )
        else:
            a_score = 85
        featured = doc.get("featured_series") or {}
        doc_series_id = str((featured.get("series") or {}).get("id") or "")
        has_any_series = bool(featured or doc.get("series_names"))
        if known_hc_series_ids and doc_series_id in known_hc_series_ids:
            series_bonus = 2
        elif has_any_series:
            series_bonus = 1
        else:
            series_bonus = 0

        above = t_score >= 90 and a_score >= 85
        candidate = {
            "hc_id": str(doc.get("id", "")),
            "title": doc_title,
            "author": doc_author,
            "slug": doc.get("slug", ""),
            "t_score": t_score,
            "a_score": a_score,
            "series_bonus": series_bonus,
            "above_threshold": above,
            "is_best": False,
            "series_names": doc.get("series_names") or [],
            "featured_series": doc.get("featured_series"),
        }
        log["candidates"].append(candidate)
        if above and (t_score, a_score, series_bonus) > best_score:
            best = doc
            best_score = (t_score, a_score, series_bonus)

    log["candidates"].sort(key=lambda c: (c["t_score"], c["a_score"], c["series_bonus"]), reverse=True)

    if best:
        for c in log["candidates"]:
            if c["hc_id"] == str(best.get("id", "")):
                c["is_best"] = True

    if not best:
        scores = [(c["t_score"], c["a_score"]) for c in log["candidates"]]
        log["result"] = "no_match"
        log["reason"] = f"Need t>=90 a>=85. Best: {max(scores, default=(0,0))}"
        return log

    hardcover_id = str(best.get("id", ""))
    hardcover_slug = best.get("slug", "")

    featured = best.get("featured_series") or {}
    featured_series_name = ((featured.get("series") or {}).get("name") or "").strip()
    featured_series_id = str((featured.get("series") or {}).get("id") or "")
    series_names = best.get("series_names") or []

    hc_contributors = []
    for c in (best.get("contributions") or best.get("cached_contributors") or []):
        if not isinstance(c, dict):
            continue
        hc_author_id = str(c.get("author_id") or (c.get("author") or {}).get("id", "") or "")
        hc_author_name = (c.get("author_name") or (c.get("author") or {}).get("name", "") or "")
        if hc_author_id and hc_author_name:
            hc_contributors.append({"id": hc_author_id, "name": hc_author_name})

    log["result"] = "match"
    log["hardcover_id"] = hardcover_id
    log["hardcover_slug"] = hardcover_slug
    return log


async def try_link_author(author_id: str, settings: dict) -> dict:
    """Run HC author match verbosely. Persists if a match is found. Returns full log."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"result": "no_api_key"}

    async with get_db() as db:
        author_row = await (
            await db.execute("SELECT name FROM authors WHERE id = ?", (author_id,))
        ).fetchone()
        if not author_row:
            return {"result": "not_found"}
        name = author_row[0]
        existing_link = await (
            await db.execute(
                "SELECT hardcover_author_id FROM author_links WHERE author_id = ?", (author_id,)
            )
        ).fetchone()

    log: dict = {
        "query": name,
        "already_linked": bool(existing_link and existing_link[0]),
        "current_hardcover_author_id": existing_link[0] if existing_link else None,
        "candidates": [],
        "result": None,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={
                    "query": 'query Search($q: String!) { search(query: $q, query_type: "author", per_page: 15) { results } }',
                    "variables": {"q": name},
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            hits = resp.json()["data"]["search"]["results"].get("hits", [])
    except Exception as e:
        log["result"] = "error"
        log["error"] = str(e)
        return log

    if not hits:
        log["result"] = "no_results"
        return log

    best = None
    best_score = 0
    for hit in hits:
        doc = hit.get("document", {})
        doc_name = doc.get("name") or ""
        score = _author_score(name, doc_name)
        above = score >= 85
        candidate = {
            "hc_id": str(doc.get("id", "")),
            "name": doc_name,
            "slug": doc.get("slug", ""),
            "score": score,
            "above_threshold": above,
            "is_best": False,
        }
        log["candidates"].append(candidate)
        if above and score > best_score:
            best = doc
            best_score = score

    log["candidates"].sort(key=lambda c: c["score"], reverse=True)

    if best:
        for c in log["candidates"]:
            if c["hc_id"] == str(best.get("id", "")):
                c["is_best"] = True

    if not best:
        log["result"] = "no_match"
        log["reason"] = f"Need score>=85. Best: {max((c['score'] for c in log['candidates']), default=0)}"
        return log

    log["result"] = "match"
    log["hardcover_author_id"] = str(best.get("id", ""))
    return log


async def try_link_series(series_id: str, settings: dict) -> dict:
    """Run HC series match verbosely. Persists if a match is found. Returns full log."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"result": "no_api_key"}

    async with get_db() as db:
        series_row = await (
            await db.execute("SELECT name FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not series_row:
            return {"result": "not_found"}
        name = series_row[0]
        existing_link = await (
            await db.execute(
                "SELECT hardcover_series_id FROM series_links WHERE series_id = ?", (series_id,)
            )
        ).fetchone()

    # Find the first book in this series that already has an HC link
    async with get_db() as db:
        first_linked = await (
            await db.execute(
                """SELECT bl.hardcover_id FROM book_series bs
                   JOIN book_links bl ON bl.book_id = bs.book_id
                   WHERE bs.series_id = ? AND bl.hardcover_id IS NOT NULL AND bl.hardcover_id != ''
                   ORDER BY CAST(bs.position AS REAL), bs.position
                   LIMIT 1""",
                (series_id,),
            )
        ).fetchone()
    first_book_hc_id = first_linked[0] if first_linked else None

    log: dict = {
        "query": name,
        "already_linked": bool(existing_link and existing_link[0]),
        "current_hardcover_series_id": existing_link[0] if existing_link else None,
        "candidates": [],
        "result": None,
    }

    # Run name search and first-book series lookup concurrently
    async def _name_search() -> list:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={
                    "query": 'query Search($q: String!) { search(query: $q, query_type: "series", per_page: 15) { results } }',
                    "variables": {"q": name},
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            return resp.json()["data"]["search"]["results"].get("hits", [])

    try:
        if first_book_hc_id:
            search_result, book_series = await asyncio.gather(
                _name_search(),
                _hc_series_for_book(first_book_hc_id, api_key),
                return_exceptions=True,
            )
            hits = search_result if isinstance(search_result, list) else []
            extra_series = book_series if isinstance(book_series, list) else []
        else:
            hits = await _name_search()
            extra_series = []
    except Exception as e:
        log["result"] = "error"
        log["error"] = str(e)
        return log

    hits = [h for h in hits if (h.get("document", {}).get("books_count") or 0) > 0]
    hits = sorted(hits, key=lambda h: h.get("document", {}).get("books_count") or 0, reverse=True)

    seen_ids: set = set()
    best = None
    best_score = 0

    for hit in hits:
        doc = hit.get("document", {})
        hc_id = str(doc.get("id", ""))
        if not hc_id or hc_id in seen_ids:
            continue
        seen_ids.add(hc_id)
        doc_name = doc.get("name") or ""
        score = fuzz.token_sort_ratio(_norm_title(name), _norm_title(doc_name))
        above = score >= 85
        candidate = {
            "hc_id": hc_id,
            "name": doc_name,
            "slug": doc.get("slug", ""),
            "score": score,
            "above_threshold": above,
            "is_best": False,
        }
        log["candidates"].append(candidate)
        if above and score > best_score:
            best = doc
            best_score = score

    # Merge series from the first linked book (not already in name-search results)
    for s in extra_series:
        hc_id = str(s.get("id", ""))
        if not hc_id or hc_id in seen_ids:
            continue
        seen_ids.add(hc_id)
        doc_name = s.get("name") or ""
        score = fuzz.token_sort_ratio(_norm_title(name), _norm_title(doc_name))
        above = score >= 85
        candidate = {
            "hc_id": hc_id,
            "name": doc_name,
            "slug": s.get("slug", ""),
            "score": score,
            "above_threshold": above,
            "is_best": False,
            "via_book": True,
        }
        log["candidates"].append(candidate)
        if above and score > best_score:
            best = s
            best_score = score

    # Sort: via_book candidates first, then by score descending
    log["candidates"].sort(key=lambda c: (0 if c.get("via_book") else 1, -c["score"]))

    if best:
        best_id = str(best.get("id", ""))
        for c in log["candidates"]:
            if c["hc_id"] == best_id:
                c["is_best"] = True

    if not best:
        log["result"] = "no_results" if not log["candidates"] else "no_match"
        if log["candidates"]:
            log["reason"] = f"Need score>=85. Best: {max((c['score'] for c in log['candidates']), default=0)}"
        return log

    log["result"] = "match"
    log["hardcover_series_id"] = str(best.get("id", ""))
    return log


async def sync_library() -> dict:
    """Fetch all ABS items and upsert into the local database."""
    from .audiobookshelf import AudiobookshelfService

    settings = await get_settings()
    await _upsert_task_state("library_sync", running=True)

    counters = {"synced": 0, "created": 0, "updated": 0, "errors": 0}
    try:
        abs_svc = AudiobookshelfService(settings.get("audiobookshelf", {}))
        if not abs_svc.base_url:
            raise ValueError("AudiobookShelf URL not configured")

        items = await abs_svc.list_all_items()
        counters["synced"] = len(items)
        seen_abs_ids = {i["abs_id"] for i in items if i.get("abs_id")}

        for item in items:
            try:
                result = await _sync_item(item)
                if result == "created":
                    counters["created"] += 1
                elif result == "updated":
                    counters["updated"] += 1
            except Exception as e:
                logger.error(f"Error syncing item {item.get('abs_id')}: {e}", exc_info=True)
                counters["errors"] += 1

        # Remove formats and clear abs links for items deleted from ABS
        if seen_abs_ids:
            placeholders = ",".join("?" * len(seen_abs_ids))
            async with get_db() as db:
                await db.execute(
                    f"DELETE FROM book_formats WHERE abs_id IS NOT NULL AND abs_id != '' AND abs_id NOT IN ({placeholders})",
                    list(seen_abs_ids),
                )
                await db.execute(
                    f"UPDATE book_links SET abs_id = NULL WHERE abs_id IS NOT NULL AND abs_id != '' AND abs_id NOT IN ({placeholders})",
                    list(seen_abs_ids),
                )
                # Delete orphaned books: no abs_id, no formats, no active requests
                orphan_rows = await (
                    await db.execute(
                        """SELECT b.id FROM books b
                           LEFT JOIN book_links bl ON bl.book_id = b.id
                           LEFT JOIN book_formats bf ON bf.book_id = b.id
                           LEFT JOIN requests r ON r.book_id = b.id
                               AND r.status NOT IN ('completed', 'failed', 'in_library')
                           WHERE (bl.abs_id IS NULL OR bl.abs_id = '')
                             AND bf.id IS NULL
                             AND r.id IS NULL"""
                    )
                ).fetchall()
                orphan_ids = [r[0] for r in orphan_rows]
                for oid in orphan_ids:
                    await db.execute("DELETE FROM book_authors WHERE book_id = ?", (oid,))
                    await db.execute("DELETE FROM book_series WHERE book_id = ?", (oid,))
                    await db.execute("DELETE FROM book_links WHERE book_id = ?", (oid,))
                    await db.execute("DELETE FROM requests WHERE book_id = ? AND status IN ('completed', 'failed', 'in_library')", (oid,))
                    await db.execute("DELETE FROM books WHERE id = ?", (oid,))

                # Remove series that have no books left (clean links first to avoid FK violation)
                await db.execute(
                    """DELETE FROM series_links WHERE series_id NOT IN (SELECT DISTINCT series_id FROM book_series)"""
                )
                await db.execute(
                    """DELETE FROM series WHERE id NOT IN (SELECT DISTINCT series_id FROM book_series)"""
                )
                await db.commit()

    except Exception as e:
        logger.error(f"sync_library failed: {e}", exc_info=True)
        await _upsert_task_state("library_sync", running=False, last_result=f"error: {e}")
        raise

    # Refresh slug/release_date for HC-linked books that are missing either,
    # or where release_date is still in the future (it may have changed).
    api_key = settings.get("hardcover", {}).get("api_key", "")
    await _hc_refresh_meta(api_key)

    await _upsert_task_state("library_sync", running=False, last_result="ok")
    return counters


async def _sync_item(item: dict) -> str:
    """Sync a single ABS item. Returns 'created', 'updated', or 'unchanged'."""
    abs_id = item.get("abs_id", "")
    if not abs_id:
        return "unchanged"

    title = (item.get("title") or "").strip()
    cover_url = item.get("cover_url") or None
    author_string = (item.get("author") or "").strip()
    # author_items carries ABS author IDs from full item fetch; fall back to splitting flat string
    raw_author_items = item.get("author_items") or []
    if raw_author_items and raw_author_items[0].get("name"):
        author_items = raw_author_items
    else:
        names = _split_authors(author_string) or ([author_string] if author_string else [])
        author_items = [{"name": n, "abs_id": ""} for n in names]
    series_items = item.get("series_items") or []
    formats = item.get("formats") or []
    now = _now()

    async with get_db() as db:
        link_row = await (
            await db.execute(
                "SELECT book_id FROM book_links WHERE abs_id = ?", (abs_id,)
            )
        ).fetchone()

        if link_row is None:
            # Check if we organised this book ourselves: a completed/downloaded request
            # for a book with no abs_id yet is an authoritative link.
            existing_book_id = None
            req_match = await (
                await db.execute(
                    """SELECT r.book_id FROM requests r
                       JOIN book_links bl ON bl.book_id = r.book_id
                       WHERE r.status IN ('completed', 'in_library', 'downloaded', 'organizing')
                         AND (bl.abs_id IS NULL OR bl.abs_id = '')
                         AND r.book_id IN (
                             SELECT b.id FROM books b WHERE lower(b.title) = lower(?)
                         )
                       LIMIT 1""",
                    (title,),
                )
            ).fetchone()
            if req_match:
                existing_book_id = req_match[0]

            if existing_book_id:
                book_id = existing_book_id
                await db.execute(
                    "UPDATE book_links SET abs_id = ?, linked_at = ? WHERE book_id = ?",
                    (abs_id, now, book_id),
                )
            else:
                book_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO books (id, title, cover_url, metadata_source, abs_checked_at, created_at, updated_at)
                       VALUES (?, ?, ?, 'abs', ?, ?, ?)""",
                    (book_id, title, cover_url, now, now, now),
                )

                for pos, ai in enumerate(author_items, 1):
                    author_id = await _get_or_create_author(db, ai["name"], ai.get("abs_id", ""))
                    await db.execute(
                        """INSERT OR IGNORE INTO book_authors (id, book_id, author_id, author_position, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), book_id, author_id, pos, now),
                    )

                for si in series_items:
                    series_id = await _get_or_create_series(db, si["name"], si.get("abs_id", ""))
                    await db.execute(
                        """INSERT OR IGNORE INTO book_series (id, book_id, series_id, position, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), book_id, series_id, _norm_pos(si.get("sequence")), now),
                    )

                await db.execute(
                    "INSERT INTO book_links (id, book_id, abs_id, linked_at) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), book_id, abs_id, now),
                )

            seen_types = set()
            for fmt in formats:
                fmt_type = fmt.get("type")
                if not fmt_type or fmt_type in seen_types:
                    continue
                seen_types.add(fmt_type)
                narrator = fmt.get("narrator") or ''
                await db.execute(
                    """INSERT INTO book_formats
                           (id, book_id, type, narrator, abs_id, abs_url, fulfilled_by_request_id, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                       ON CONFLICT(book_id, type) DO UPDATE SET
                           narrator = excluded.narrator,
                           abs_id   = excluded.abs_id,
                           abs_url  = excluded.abs_url,
                           updated_at = excluded.updated_at""",
                    (str(uuid.uuid4()), book_id, fmt_type, narrator,
                     abs_id, item.get("abs_url"), now, now),
                )
                # Drop any non-pending requests for this type — format is now in library
                await db.execute(
                    "DELETE FROM requests WHERE book_id=? AND type=? AND status NOT IN ('pending','failed','rejected')",
                    (book_id, fmt_type),
                )
            await db.commit()

        else:
            book_id = link_row[0]
            changed = False

            book_row = await (
                await db.execute("SELECT title, cover_url FROM books WHERE id = ?", (book_id,))
            ).fetchone()

            updates = {}
            if book_row["title"] != title:
                updates["title"] = title
            if book_row["cover_url"] != cover_url:
                updates["cover_url"] = cover_url
            if updates:
                set_clause = ", ".join(f"{k} = ?" for k in updates)
                await db.execute(
                    f"UPDATE books SET {set_clause}, updated_at = ? WHERE id = ?",
                    (*updates.values(), now, book_id),
                )
                changed = True

            for pos, ai in enumerate(author_items, 1):
                author_id = await _get_or_create_author(db, ai["name"], ai.get("abs_id", ""))
                r = await db.execute(
                    """INSERT OR IGNORE INTO book_authors (id, book_id, author_id, author_position, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), book_id, author_id, pos, now),
                )
                if r.rowcount:
                    changed = True

            current_series_ids = []
            for si in series_items:
                series_id = await _get_or_create_series(db, si["name"], si.get("abs_id", ""))
                current_series_ids.append(series_id)
                r = await db.execute(
                    """INSERT OR IGNORE INTO book_series (id, book_id, series_id, position, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), book_id, series_id, _norm_pos(si.get("sequence")), now),
                )
                if r.rowcount:
                    changed = True

            # Remove series links that are no longer present in ABS.
            # Only trim when ABS actually reported series for this book — if it returned
            # none, that means ABS metadata is incomplete, not that the links are wrong.
            if current_series_ids:
                placeholders = ",".join("?" * len(current_series_ids))
                r = await db.execute(
                    f"DELETE FROM book_series WHERE book_id = ? AND series_id NOT IN ({placeholders})",
                    [book_id, *current_series_ids],
                )
                if r.rowcount:
                    changed = True

            seen_types = set()
            for fmt in formats:
                fmt_type = fmt.get("type")
                if not fmt_type or fmt_type in seen_types:
                    continue
                seen_types.add(fmt_type)
                narrator = fmt.get("narrator") or ''
                r = await db.execute(
                    """INSERT INTO book_formats
                           (id, book_id, type, narrator, abs_id, abs_url, fulfilled_by_request_id, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                       ON CONFLICT(book_id, type) DO UPDATE SET
                           narrator = excluded.narrator,
                           abs_id   = excluded.abs_id,
                           abs_url  = excluded.abs_url,
                           updated_at = excluded.updated_at""",
                    (str(uuid.uuid4()), book_id, fmt_type, narrator,
                     abs_id, item.get("abs_url"), now, now),
                )
                if r.rowcount:
                    changed = True
                # Drop any non-pending requests for this type — format is now in library
                await db.execute(
                    "DELETE FROM requests WHERE book_id=? AND type=? AND status NOT IN ('pending','failed','rejected')",
                    (book_id, fmt_type),
                )

            await db.execute("UPDATE books SET abs_checked_at = ? WHERE id = ?", (now, book_id))
            await db.commit()

    if link_row is None:
        return "created"
    else:
        return "updated" if changed else "unchanged"
