import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone

import httpx
from rapidfuzz import fuzz

from ..database import get_db
from ..settings import get_settings

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
                """SELECT a.name FROM authors a
                   JOIN book_authors ba ON ba.author_id = a.id
                   WHERE ba.book_id = ?
                   ORDER BY ba.author_position""",
                (book_id,),
            )
        ).fetchall()
        author = author_rows[0][0] if author_rows else ""

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

    await asyncio.sleep(0.25)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={
                    "query": """
                    query Search($q: String!) {
                      search(query: $q, query_type: "Book", per_page: 5) {
                        results
                      }
                    }
                    """,
                    "variables": {"q": query},
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"HC link search failed for book {book_id}: {e}")
        return False

    try:
        hits = data["data"]["search"]["results"].get("hits", [])
    except Exception:
        return False

    best = None
    best_score = (0, 0)
    for hit in hits:
        doc = hit.get("document", {})
        doc_title = doc.get("title", "") or ""
        contributors = doc.get("contributions") or doc.get("cached_contributors") or []
        doc_author = ""
        if contributors and isinstance(contributors[0], dict):
            doc_author = (
                contributors[0].get("author_name")
                or (contributors[0].get("author") or {}).get("name", "")
                or ""
            )

        t_score = fuzz.token_sort_ratio(title.lower(), doc_title.lower())
        a_score = fuzz.token_sort_ratio(author.lower(), doc_author.lower()) if author else 85

        if t_score >= 90 and a_score >= 85 and (t_score, a_score) > best_score:
            best = doc
            best_score = (t_score, a_score)

    if not best:
        return False

    hardcover_id = str(best.get("id", ""))
    hardcover_slug = best.get("slug", "")
    if not hardcover_id:
        return False

    hc_series = []
    for bs in (best.get("book_series") or []):
        s = bs.get("series") or {}
        if s.get("id"):
            hc_series.append({"id": str(s["id"]), "name": s.get("name", "")})

    async with get_db() as db:
        await db.execute(
            "UPDATE book_links SET hardcover_id = ?, hardcover_slug = ? WHERE book_id = ?",
            (hardcover_id, hardcover_slug, book_id),
        )
        for local_series_id, local_series_name in book_series_rows:
            best_hc = None
            best_s_score = 0
            for hs in hc_series:
                score = fuzz.token_sort_ratio(local_series_name.lower(), hs["name"].lower())
                if score >= 80 and score > best_s_score:
                    best_hc = hs
                    best_s_score = score
            if best_hc:
                await db.execute(
                    "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ?",
                    (best_hc["id"], local_series_id),
                )
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
                result = await _sync_item(item, settings)
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


async def _sync_item(item: dict, settings: dict) -> str:
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

            hc_link = await (
                await db.execute(
                    "SELECT hardcover_id FROM book_links WHERE book_id = ?", (book_id,)
                )
            ).fetchone()

    # HC linking outside DB transaction (makes network calls)
    if link_row is None:
        await _link_to_hardcover(book_id, settings)
        return "created"
    else:
        if hc_link and hc_link[0] is None:
            linked = await _link_to_hardcover(book_id, settings)
            if linked:
                changed = True
        return "updated" if changed else "unchanged"
