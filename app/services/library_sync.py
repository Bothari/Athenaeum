import asyncio
import logging
import re
import time
import uuid
from datetime import datetime, timezone

import httpx
from rapidfuzz import fuzz

from ..database import get_db
from ..settings import get_settings

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


async def _set_hc_author_id(db, author_id: str, hc_author_id: str) -> bool:
    """Set hardcover_author_id on author_links, skipping if already claimed. Returns True if set."""
    conflict = await (
        await db.execute(
            "SELECT author_id FROM author_links WHERE hardcover_author_id = ?", (hc_author_id,)
        )
    ).fetchone()
    if conflict and conflict[0] != author_id:
        logger.warning(f"HC author {hc_author_id} already linked to {conflict[0]}, skipping {author_id}")
        return False
    await db.execute(
        "UPDATE author_links SET hardcover_author_id = ? WHERE author_id = ? AND (hardcover_author_id IS NULL OR hardcover_author_id = '')",
        (hc_author_id, author_id),
    )
    return True


async def _get_or_create_author(db, name: str, abs_author_id: str = "") -> str:
    """Return author_id, creating author and author_links rows if needed."""
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


async def _get_or_create_series(db, name: str, abs_series_id: str = "") -> str:
    """Return series_id, creating series and series_links rows if needed."""
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


async def _hc_book_search(query: str, api_key: str, pages: int = 3) -> list:
    """Fetch up to `pages` pages of HC book search results concurrently.

    HC caps per_page at 25, so we fan out across pages and merge.
    Returns hits sorted by users_count descending.
    """
    gql = 'query Search($q: String!, $page: Int!) { search(query: $q, query_type: "Book", per_page: 25, page: $page) { results } }'
    headers = {"Authorization": f"Bearer {api_key}"}

    async def fetch_page(client: httpx.AsyncClient, page: int) -> list:
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
            *[fetch_page(client, p) for p in range(1, pages + 1)],
            return_exceptions=True,
        )

    hits = []
    for r in results:
        if isinstance(r, list):
            hits.extend(r)

    seen = set()
    deduped = []
    for h in hits:
        doc_id = h.get("document", {}).get("id")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            deduped.append(h)

    return sorted(deduped, key=lambda h: h.get("document", {}).get("users_count") or 0, reverse=True)


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
                """SELECT bs.series_id, s.name FROM book_series bs
                   JOIN series s ON s.id = bs.series_id
                   WHERE bs.book_id = ?""",
                (book_id,),
            )
        ).fetchall()

    query = f"{title} {author}".strip()
    if not query:
        return False

    try:
        hits = await _hc_book_search(query, api_key)
    except httpx.HTTPStatusError:
        raise
    except Exception as e:
        logger.warning(f"HC link search failed for book {book_id}: {e}")
        return False

    if not hits:
        logger.debug(f"HC no results for '{title}' by '{author}'")
        return False

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

        logger.debug(f"HC candidate '{doc_title}' by '{doc_author}': t={t_score} a={a_score}")

        if t_score >= 90 and a_score >= 85 and (t_score, a_score) > best_score:
            best = doc
            best_score = (t_score, a_score)

    if not best:
        logger.warning(f"HC no confident match for '{title}' by '{author}' (best scores: {best_score})")
        return False

    hardcover_id = str(best.get("id", ""))
    hardcover_slug = best.get("slug", "")
    if not hardcover_id:
        return False

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
        for local_series_id, local_series_name in book_series_rows:
            best_match_name = None
            best_s_score = 0
            for sname in series_names:
                score = fuzz.token_sort_ratio(local_series_name.lower(), sname.lower())
                if score >= 80 and score > best_s_score:
                    best_match_name = sname
                    best_s_score = score
            if best_match_name and featured_series_id and featured_series_name:
                if fuzz.token_sort_ratio(best_match_name.lower(), featured_series_name.lower()) >= 80:
                    await db.execute(
                        "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ? AND (hardcover_series_id IS NULL OR hardcover_series_id = '')",
                        (featured_series_id, local_series_id),
                    )
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


async def _hc_rate_limited_loop(items: list, fn, deadline: float) -> dict:
    """Run fn(item) for each item, rate-limited to ~60 req/min with exponential backoff on 429."""
    counters = {"linked": 0, "failed": 0, "skipped": 0}
    backoff = 0.0
    for i, item in enumerate(items):
        if time.monotonic() >= deadline:
            counters["skipped"] = len(items) - i
            break
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
                logger.warning(f"HC rate limited, backing off {backoff:.0f}s")
            else:
                logger.warning(f"HC HTTP error: {e}")
                backoff = 0.0
            counters["failed"] += 1
    return counters


async def _hc_link_books(settings: dict, deadline: float) -> dict:
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
        book_ids, lambda bid: _link_to_hardcover(bid, settings), deadline
    )


async def _hc_catchup_authors(settings: dict, deadline: float) -> dict:
    """Catch-up pass: link authors with no hardcover_author_id via HC author search."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"linked": 0, "failed": 0, "skipped": 0}

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT al.author_id, a.name FROM author_links al
                   JOIN authors a ON a.id = al.author_id
                   WHERE al.hardcover_author_id IS NULL OR al.hardcover_author_id = ''
                   ORDER BY al.linked_at"""
            )
        ).fetchall()

    async def link_author(row) -> bool:
        author_id, name = row["author_id"], row["name"]
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
        if not hc_author_id:
            return False

        async with get_db() as db:
            linked = await _set_hc_author_id(db, author_id, hc_author_id)
            await db.commit()
        return linked

    return await _hc_rate_limited_loop(list(rows), link_author, deadline)


async def _hc_catchup_series(settings: dict, deadline: float) -> dict:
    """Catch-up pass: link series with no hardcover_series_id via HC series search."""
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"linked": 0, "failed": 0, "skipped": 0}

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT sl.series_id, s.name FROM series_links sl
                   JOIN series s ON s.id = sl.series_id
                   WHERE sl.hardcover_series_id IS NULL OR sl.hardcover_series_id = ''
                   ORDER BY sl.linked_at"""
            )
        ).fetchall()

    async def link_series(row) -> bool:
        series_id, name = row["series_id"], row["name"]
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

        hits = sorted(hits, key=lambda h: h.get("document", {}).get("books_count") or 0, reverse=True)

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
        if not hc_series_id:
            return False

        async with get_db() as db:
            await db.execute(
                "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ? AND (hardcover_series_id IS NULL OR hardcover_series_id = '')",
                (hc_series_id, series_id),
            )
            await db.commit()
        return True

    return await _hc_rate_limited_loop(list(rows), link_series, deadline)


async def cache_refresh() -> dict:
    """HC linking: books (primary), then author/series catch-up. Rate-limited, 1hr time slice."""
    settings = await get_settings()
    deadline = time.monotonic() + 3600
    await _upsert_task_state("cache_refresh", running=True)
    try:
        b = await _hc_link_books(settings, deadline)
        a = await _hc_catchup_authors(settings, deadline)
        s = await _hc_catchup_series(settings, deadline)
        result = (
            f"books {b['linked']}/{b['linked']+b['failed']} linked"
            + (f" ({b['skipped']} skipped)" if b['skipped'] else "")
            + f" | authors {a['linked']}/{a['linked']+a['failed']}"
            + f" | series {s['linked']}/{s['linked']+s['failed']}"
        )
        logger.info(f"cache_refresh complete: {result}")
        await _upsert_task_state("cache_refresh", running=False, last_result=result)
        return {"books": b, "authors": a, "series": s}
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
                """SELECT bs.series_id, s.name FROM book_series bs
                   JOIN series s ON s.id = bs.series_id
                   WHERE bs.book_id = ?""",
                (book_id,),
            )
        ).fetchall()

        existing_link = await (
            await db.execute(
                "SELECT hardcover_id FROM book_links WHERE book_id = ?", (book_id,)
            )
        ).fetchone()

    query = f"{title} {author}".strip()
    log: dict = {
        "query": query,
        "title": title,
        "author": author,
        "already_linked": bool(existing_link and existing_link[0]),
        "current_hardcover_id": existing_link[0] if existing_link else None,
        "candidates": [],
        "result": None,
    }

    try:
        hits = await _hc_book_search(query, api_key)
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
        above = t_score >= 90 and a_score >= 85
        candidate = {
            "hc_id": str(doc.get("id", "")),
            "title": doc_title,
            "author": doc_author,
            "slug": doc.get("slug", ""),
            "t_score": t_score,
            "a_score": a_score,
            "above_threshold": above,
            "is_best": False,
            "series_names": doc.get("series_names") or [],
            "featured_series": doc.get("featured_series"),
        }
        log["candidates"].append(candidate)
        if above and (t_score, a_score) > best_score:
            best = doc
            best_score = (t_score, a_score)

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

    async with get_db() as db:
        conflict = await (
            await db.execute(
                "SELECT book_id FROM book_links WHERE hardcover_id = ?", (hardcover_id,)
            )
        ).fetchone()
        if conflict and conflict[0] != book_id:
            log["result"] = "conflict"
            log["conflict_book_id"] = conflict[0]
            return log

        await db.execute(
            "UPDATE book_links SET hardcover_id = ?, hardcover_slug = ? WHERE book_id = ?",
            (hardcover_id, hardcover_slug, book_id),
        )
        series_linked = []
        for local_series_id, local_series_name in book_series_rows:
            best_match_name = None
            best_s_score = 0
            for sname in series_names:
                score = fuzz.token_sort_ratio(local_series_name.lower(), sname.lower())
                if score >= 80 and score > best_s_score:
                    best_match_name = sname
                    best_s_score = score
            if best_match_name and featured_series_id and featured_series_name:
                if fuzz.token_sort_ratio(best_match_name.lower(), featured_series_name.lower()) >= 80:
                    await db.execute(
                        "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ? AND (hardcover_series_id IS NULL OR hardcover_series_id = '')",
                        (featured_series_id, local_series_id),
                    )
                    series_linked.append({"local": local_series_name, "hc_id": featured_series_id})
        author_linked = []
        for local_author in author_rows:
            best_hc_author = None
            best_a_score = 0
            for hc in hc_contributors:
                score = _author_score(local_author["name"], hc["name"])
                if score >= 85 and score > best_a_score:
                    best_hc_author = hc
                    best_a_score = score
            if best_hc_author:
                if await _set_hc_author_id(db, local_author["id"], best_hc_author["id"]):
                    author_linked.append({"local": local_author["name"], "hc_id": best_hc_author["id"]})
        await db.commit()

    log["result"] = "linked"
    log["hardcover_id"] = hardcover_id
    log["hardcover_slug"] = hardcover_slug
    log["series_linked"] = series_linked
    log["authors_linked"] = author_linked
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
            "score": score,
            "above_threshold": above,
            "is_best": False,
        }
        log["candidates"].append(candidate)
        if above and score > best_score:
            best = doc
            best_score = score

    if best:
        for c in log["candidates"]:
            if c["hc_id"] == str(best.get("id", "")):
                c["is_best"] = True

    if not best:
        log["result"] = "no_match"
        log["reason"] = f"Need score>=85. Best: {max((c['score'] for c in log['candidates']), default=0)}"
        return log

    hc_author_id = str(best.get("id", ""))
    async with get_db() as db:
        linked = await _set_hc_author_id(db, author_id, hc_author_id)
        await db.commit()

    log["result"] = "linked" if linked else "conflict"
    log["hardcover_author_id"] = hc_author_id
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

    log: dict = {
        "query": name,
        "already_linked": bool(existing_link and existing_link[0]),
        "current_hardcover_series_id": existing_link[0] if existing_link else None,
        "candidates": [],
        "result": None,
    }

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
            resp.raise_for_status()
            hits = resp.json()["data"]["search"]["results"].get("hits", [])
    except Exception as e:
        log["result"] = "error"
        log["error"] = str(e)
        return log

    if not hits:
        log["result"] = "no_results"
        return log

    hits = sorted(hits, key=lambda h: h.get("document", {}).get("books_count") or 0, reverse=True)

    best = None
    best_score = 0
    for hit in hits:
        doc = hit.get("document", {})
        doc_name = doc.get("name") or ""
        score = fuzz.token_sort_ratio(_norm_title(name), _norm_title(doc_name))
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

    if best:
        for c in log["candidates"]:
            if c["hc_id"] == str(best.get("id", "")):
                c["is_best"] = True

    if not best:
        log["result"] = "no_match"
        log["reason"] = f"Need score>=85. Best: {max((c['score'] for c in log['candidates']), default=0)}"
        return log

    hc_series_id = str(best.get("id", ""))
    async with get_db() as db:
        await db.execute(
            "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ? AND (hardcover_series_id IS NULL OR hardcover_series_id = '')",
            (hc_series_id, series_id),
        )
        await db.commit()

    log["result"] = "linked"
    log["hardcover_series_id"] = hc_series_id
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

    except Exception as e:
        logger.error(f"sync_library failed: {e}", exc_info=True)
        await _upsert_task_state("library_sync", running=False, last_result=f"error: {e}")
        raise

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
                    (str(uuid.uuid4()), book_id, series_id, si.get("sequence") or None, now),
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
                narrator = fmt.get("narrator") or None
                await db.execute(
                    """INSERT INTO requests (id, book_id, type, status, narrator, abs_id, abs_url, created_at, updated_at)
                       VALUES (?, ?, ?, 'in_library', ?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), book_id, fmt_type, narrator,
                     abs_id, item.get("abs_url"), now, now),
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

            for si in series_items:
                series_id = await _get_or_create_series(db, si["name"], si.get("abs_id", ""))
                r = await db.execute(
                    """INSERT OR IGNORE INTO book_series (id, book_id, series_id, position, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), book_id, series_id, si.get("sequence") or None, now),
                )
                if r.rowcount:
                    changed = True

            existing_rows = await (
                await db.execute(
                    "SELECT type FROM requests WHERE book_id = ? AND status = 'in_library'",
                    (book_id,),
                )
            ).fetchall()
            existing_types = {r[0] for r in existing_rows}
            seen_types = set()
            for fmt in formats:
                fmt_type = fmt.get("type")
                if not fmt_type or fmt_type in seen_types:
                    continue
                seen_types.add(fmt_type)
                if fmt_type not in existing_types:
                    narrator = fmt.get("narrator") or None
                    await db.execute(
                        """INSERT INTO requests (id, book_id, type, status, narrator, abs_id, abs_url, created_at, updated_at)
                           VALUES (?, ?, ?, 'in_library', ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), book_id, fmt_type, narrator,
                         abs_id, item.get("abs_url"), now, now),
                    )
                    changed = True

            await db.execute("UPDATE books SET abs_checked_at = ? WHERE id = ?", (now, book_id))
            await db.commit()

    if link_row is None:
        return "created"
    else:
        return "updated" if changed else "unchanged"
