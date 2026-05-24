"""Auto-search: find the best Prowlarr result for a request and snatch it."""
import logging
import re
import uuid
from datetime import date, datetime, timezone

from ..database import get_db
from ..settings import get_settings
from ..services.download_clients import (
    prowlarr_search, build_prowlarr_query,
    get_torrent_client, get_usenet_client, _detect_format, _score_result,
)
from ..services.request_events import log_request_event, set_request_status

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Series-pack detection ──────────────────────────────────────────────────────

_SERIES_PACK_RE = re.compile(
    r'complete\s+(series|collection|set)'
    r'|box\s+set'
    r'|omnibus'
    r'|books?\s+\d+[-–—]\d+'
    r'|\d+[\s-]books?\b'
    r'|the\s+complete\b',
    re.IGNORECASE,
)


def is_series_pack(title: str) -> bool:
    """Return True if a Prowlarr result title looks like a multi-book series pack."""
    if _SERIES_PACK_RE.search(title):
        return True
    # Three or more titles separated by & or / suggest multiple books in one release
    return len(re.findall(r'\s+[&/]\s+', title)) >= 2


# ── Result ranking ─────────────────────────────────────────────────────────────

def rank_results(
    results: list[dict],
    ranking: list[dict],
    allowed_formats: list[str],
    min_seeders: int,
    filter_series_packs: bool = True,
) -> list[dict]:
    """Filter results by hard constraints then sort by user-configured ranking stack.

    Hard filters (applied before ranking):
    - Format not in allowed_formats (if format is detectable)
    - Looks like a series pack (skipped when filter_series_packs=False)
    - Below minimum seeder count (torrent only)
    """
    allowed_lower = {f.lower() for f in allowed_formats}

    def passes(r: dict) -> bool:
        fmt = _detect_format(r.get("title", ""))
        if fmt is not None and fmt not in allowed_lower:
            return False
        if filter_series_packs and is_series_pack(r.get("title", "")):
            return False
        if r.get("protocol") == "torrent" and min_seeders > 0:
            if (r.get("seeders") or 0) < min_seeders:
                return False
        return True

    filtered = [r for r in results if passes(r)]
    if not filtered or not ranking:
        return filtered

    format_order = {f.lower(): i for i, f in enumerate(allowed_formats)}
    n_formats = len(allowed_formats)

    def sort_key(r: dict) -> list:
        key = []
        for criterion in ranking:
            if not criterion.get("enabled", True):
                continue
            c = criterion["criterion"]
            if c == "format":
                fmt = _detect_format(r.get("title", "")) or ""
                key.append(format_order.get(fmt, n_formats))
            elif c == "seeders":
                key.append(-(r.get("seeders") or 0))
            elif c == "size":
                size = r.get("size") or 0
                key.append(-size if criterion.get("prefer", "larger") == "larger" else size)
            elif c == "age":
                age = r.get("age") or 0
                key.append(age if criterion.get("prefer", "newer") == "newer" else -age)
            elif c == "indexer_priority":
                key.append(r.get("indexerPriority") or 999)
        return key

    return sorted(filtered, key=sort_key)


# ── Task-state helpers ─────────────────────────────────────────────────────────

async def _set_task_running(msg: str):
    async with get_db() as db:
        await db.execute(
            """INSERT INTO task_state (task, running, last_result) VALUES ('auto_search', 1, ?)
               ON CONFLICT(task) DO UPDATE SET running = 1, last_result = ?""",
            (msg, msg),
        )
        await db.commit()


async def _set_task_done(result: str):
    now = _now()
    async with get_db() as db:
        await db.execute(
            """INSERT INTO task_state (task, running, last_run, last_result) VALUES ('auto_search', 0, ?, ?)
               ON CONFLICT(task) DO UPDATE SET running = 0, last_run = ?, last_result = ?""",
            (now, result, now, result),
        )
        await db.commit()


# ── Per-request search ─────────────────────────────────────────────────────────

async def auto_search_request(request_id: str) -> bool:
    """Search Prowlarr for the given request and snatch the best result.

    Returns True if a result was snatched, False otherwise.
    Does not check search_on_request — callers are responsible for that gate.
    """
    settings = await get_settings()
    auto_cfg = settings.get("auto_search", {})
    prowlarr_cfg = settings.get("prowlarr", {})
    if not prowlarr_cfg.get("url") or not prowlarr_cfg.get("api_key"):
        return False

    async with get_db() as db:
        row = await (
            await db.execute(
                """SELECT r.id, r.type, r.narrator, r.search_count, r.book_id, b.title,
                          b.release_date,
                          (SELECT a.name FROM authors a
                           JOIN book_authors ba ON ba.author_id = a.id
                           WHERE ba.book_id = r.book_id
                           ORDER BY ba.author_position LIMIT 1) as author
                   FROM requests r JOIN books b ON b.id = r.book_id
                   WHERE r.id = ? AND r.status = 'requested'""",
                (request_id,),
            )
        ).fetchone()

    if not row:
        return False

    release_date = row["release_date"] or ""
    if release_date and release_date > date.today().isoformat():
        logger.info("auto_search: skipping %s — not yet released (%s)", request_id, release_date)
        return False

    max_attempts = int(auto_cfg.get("max_attempts", 10))
    if row["search_count"] >= max_attempts:
        logger.info("auto_search: skipping %s — max attempts reached", request_id)
        return False

    now = _now()
    async with get_db() as db:
        await db.execute(
            "UPDATE requests SET search_count = search_count + 1, last_searched_at = ? WHERE id = ?",
            (now, request_id),
        )
        await db.commit()

    general = settings.get("general", {})
    fmt_key = "allowed_audiobook_formats" if row["type"] == "audiobook" else "allowed_ebook_formats"
    allowed_formats = general.get(fmt_key) or []
    min_seeders = int(auto_cfg.get("min_seeders", 1))
    ranking = auto_cfg.get("ranking") or []

    book_id = row["book_id"]

    try:
        query = build_prowlarr_query(row["title"], row["author"] or "")
        results = await prowlarr_search(
            prowlarr_cfg, query,
            book_type=row["type"],
            title=row["title"],
            author=row["author"] or "",
        )
    except Exception as e:
        logger.warning("auto_search: Prowlarr failed for %s: %s", request_id, e)
        async with get_db() as db:
            await log_request_event(db, request_id, "auto_search_failed",
                                    {"reason": f"Prowlarr error: {e}"}, book_id=book_id)
            await db.commit()
        return False

    ranked = rank_results(results, ranking, allowed_formats, min_seeders)

    if not ranked:
        logger.info("auto_search: no usable results for %s (%s)", request_id, row["title"])
        async with get_db() as db:
            await log_request_event(db, request_id, "auto_search_no_results",
                                    {"query": query, "total_results": len(results)}, book_id=book_id)
            await db.commit()
        return False

    best = ranked[0]

    best_score = _score_result(best.get("title", ""), row["title"], row["author"] or "")
    if best_score < 60:
        logger.info(
            "auto_search: skipping %s — best result score too low (%d): %r",
            request_id, best_score, best.get("title"),
        )
        async with get_db() as db:
            await log_request_event(db, request_id, "auto_search_no_results",
                                    {"query": query, "total_results": len(results),
                                     "filtered": len(ranked), "best_score": best_score,
                                     "best_title": best.get("title")}, book_id=book_id)
            await db.commit()
        return False

    protocol = best.get("protocol")
    download_url = best.get("downloadUrl") or ""
    if not download_url:
        return False

    if protocol == "torrent":
        client, client_name = get_torrent_client(settings)
    elif protocol == "usenet":
        client, client_name = get_usenet_client(settings)
    else:
        return False

    if not client:
        logger.warning("auto_search: no %s client configured for %s", protocol, request_id)
        return False

    try:
        download_id = await client.add(download_url)
    except Exception as e:
        logger.warning("auto_search: download client error for %s: %s", request_id, e)
        async with get_db() as db:
            await log_request_event(db, request_id, "auto_search_failed",
                                    {"reason": f"download client: {e}"}, book_id=book_id)
            await db.commit()
        return False

    dl_id = str(uuid.uuid4())
    now = _now()
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO downloads
               (id, request_id, title, indexer, guid, info_url, protocol,
                size, download_client, download_id, status, grabbed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'snatched', ?)""",
            (dl_id, request_id, best.get("title"), best.get("indexer"),
             best.get("guid"), best.get("infoUrl"), protocol,
             best.get("size"), client_name, download_id, now),
        )
        await log_request_event(db, request_id, "auto_search_snatched", {
            "title": best.get("title"),
            "indexer": best.get("indexer"),
            "protocol": protocol,
            "size": best.get("size"),
            "seeders": best.get("seeders"),
            "format": _detect_format(best.get("title", "")),
        }, book_id=book_id)
        await set_request_status(db, request_id, "snatched", now, book_id=book_id)
        await db.commit()

    logger.info("auto_search: snatched %r for request %s", best.get("title"), request_id)
    return True


# ── Bulk run (scheduled task + manual trigger) ─────────────────────────────────

async def run_auto_search_all():
    """Search all pending requests. Called by the task loop and the manual /sync/auto-search endpoint."""
    settings = await get_settings()
    auto_cfg = settings.get("auto_search", {})
    max_attempts = int(auto_cfg.get("max_attempts", 10))

    today = date.today().isoformat()
    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT r.id FROM requests r JOIN books b ON b.id = r.book_id
                   WHERE r.status = 'requested' AND r.search_count < ?
                   AND (b.release_date IS NULL OR b.release_date = '' OR b.release_date <= ?)""",
                (max_attempts, today),
            )
        ).fetchall()

    if not rows:
        await _set_task_done("no pending requests")
        return

    await _set_task_running(f"searching {len(rows)} request(s)...")

    snatched = 0
    errors = 0
    for row in rows:
        try:
            if await auto_search_request(row["id"]):
                snatched += 1
        except Exception as e:
            errors += 1
            logger.warning("auto_search: failed for request %s: %s", row["id"], e)

    parts = [f"{snatched}/{len(rows)} snatched"]
    if errors:
        parts.append(f"{errors} errors")
    await _set_task_done(", ".join(parts))
