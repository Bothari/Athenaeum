import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_admin, require_auth
from ..database import get_db
from ..services import book_search as _book_search
from ..settings import get_settings

logger = __import__("logging").getLogger(__name__)

router = APIRouter(prefix="/api")

VALID_BOOK_SORTS = {"title", "author", "created_at"}
VALID_DIR = {"asc", "desc"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _book_row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "cover_url": row["cover_url"],
        "metadata_source": row["metadata_source"],
        "metadata_url": row["metadata_url"],
        "abs_checked_at": row["abs_checked_at"],
        "release_date": row["release_date"],
        "release_date_fetched": bool(row["release_date_fetched"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/books")
async def list_books(
    q: str = Query(default=""),
    sort: str = Query(default="title"),
    dir: str = Query(default="asc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unlinked: bool = Query(default=False),
):
    if sort not in VALID_BOOK_SORTS:
        sort = "title"
    if dir not in VALID_DIR:
        dir = "asc"

    if sort == "author":
        order_expr = "(SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id WHERE ba.book_id = b.id ORDER BY ba.author_position LIMIT 1)"
    elif sort == "title":
        order_expr = "lower(b.title)"
    else:
        order_expr = f"b.{sort}"

    joins = ""
    conditions = []
    bind: list = []

    if unlinked:
        joins = " JOIN book_links bl ON bl.book_id = b.id"
        conditions.append("(bl.hardcover_id IS NULL OR bl.hardcover_id = '')")

    if q:
        import unicodedata
        qf = unicodedata.normalize("NFD", q.lower()).encode("ascii", "ignore").decode("ascii")
        like = f"%{qf}%"
        conditions.append(
            "(fold(b.title) LIKE ? OR EXISTS ("
            "SELECT 1 FROM authors a JOIN book_authors ba ON ba.author_id = a.id "
            "WHERE ba.book_id = b.id AND fold(a.name) LIKE ?))"
        )
        bind.extend([like, like])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_db() as db:
        count_row = await (
            await db.execute(f"SELECT COUNT(*) FROM books b{joins} {where}", bind)
        ).fetchone()
        rows = await (
            await db.execute(
                f"SELECT b.* FROM books b{joins} {where} ORDER BY {order_expr} {dir} LIMIT ? OFFSET ?",
                bind + [limit, offset],
            )
        ).fetchall()

        items = []
        for row in rows:
            book = _book_row_to_dict(row)
            book["authors"] = await _get_book_authors(db, row["id"])
            book["series"] = await _get_book_series(db, row["id"])
            book["link"] = await _get_book_link(db, row["id"])
            book["requests"] = await _get_book_requests(db, row["id"])
            book["formats"] = await _get_book_formats(db, row["id"])
            if book["link"].get("abs_id"):
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}?t={book.get('updated_at','')}"
            items.append(book)

    return {"items": items, "total": count_row[0], "limit": limit, "offset": offset}


@router.get("/books/{book_id}")
async def get_book(book_id: str):
    async with get_db() as db:
        row = await (
            await db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")
        book = _book_row_to_dict(row)
        book["authors"] = await _get_book_authors(db, book_id)
        book["series"] = await _get_book_series(db, book_id)
        book["link"] = await _get_book_link(db, book_id)
        book["requests"] = await _get_book_requests(db, book_id)
        book["formats"] = await _get_book_formats(db, book_id)
        if book["link"].get("abs_id"):
            book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}?t={book.get('updated_at','')}"
    return book


@router.get("/authors")
async def list_authors(
    q: str = Query(default=""),
    sort: str = Query(default="name"),
    dir: str = Query(default="asc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unlinked: bool = Query(default=False),
):
    if sort not in {"name", "book_count"}:
        sort = "name"
    if dir not in VALID_DIR:
        dir = "asc"

    order_expr = "lower(a.name)" if sort == "name" else f"book_count {dir}, lower(a.name)"
    order_clause = f"{order_expr} {dir}" if sort == "name" else order_expr

    joins = ""
    conditions = []
    bind: list = []

    if unlinked:
        joins = " JOIN author_links al ON al.author_id = a.id"
        conditions.append("(al.hardcover_author_id IS NULL OR al.hardcover_author_id = '')")

    if q:
        import unicodedata
        qf = unicodedata.normalize("NFD", q.lower()).encode("ascii", "ignore").decode("ascii")
        like = f"%{qf}%"
        conditions.append("fold(a.name) LIKE ?")
        bind.append(like)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_db() as db:
        count_row = await (
            await db.execute(f"SELECT COUNT(*) FROM authors a{joins} {where}", bind)
        ).fetchone()
        rows = await (
            await db.execute(
                f"""SELECT a.*, COUNT(ba.book_id) as book_count
                    FROM authors a{joins}
                    LEFT JOIN book_authors ba ON ba.author_id = a.id
                    {where}
                    GROUP BY a.id
                    ORDER BY {order_clause}
                    LIMIT ? OFFSET ?""",
                bind + [limit, offset],
            )
        ).fetchall()

        items = []
        for row in rows:
            link_row = await (
                await db.execute(
                    "SELECT hardcover_author_id, hardcover_author_slug FROM author_links WHERE author_id = ?",
                    (row["id"],),
                )
            ).fetchone()
            items.append({
                "id": row["id"],
                "name": row["name"],
                "book_count": row["book_count"],
                "link": {
                    "hardcover_author_id": link_row["hardcover_author_id"] if link_row else None,
                    "hardcover_author_slug": link_row["hardcover_author_slug"] if link_row else None,
                },
            })

    return {"items": items, "total": count_row[0], "limit": limit, "offset": offset}


@router.get("/authors/{author_id}/also-by")
async def get_author_also_by(author_id: str):
    """Return books by this author on Hardcover that aren't in the local library."""
    async with get_db() as db:
        author_row = await (
            await db.execute("SELECT id FROM authors WHERE id = ?", (author_id,))
        ).fetchone()
        if not author_row:
            raise HTTPException(status_code=404, detail="Author not found")

        link_row = await (
            await db.execute(
                "SELECT hardcover_author_id FROM author_links WHERE author_id = ?",
                (author_id,),
            )
        ).fetchone()
        hc_author_id = (link_row["hardcover_author_id"] if link_row else None) or ""
        if not hc_author_id:
            return {"items": [], "error": "Author not linked to Hardcover"}

        settings = await get_settings()
        api_key = settings.get("hardcover", {}).get("api_key", "")
        if not api_key:
            return {"items": [], "error": "Hardcover API key not configured"}

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        cache_row = await (
            await db.execute(
                "SELECT results_json FROM metadata_cache WHERE query = ? AND source = ? AND expires_at > ?",
                (hc_author_id, "author_books_rich", now_iso),
            )
        ).fetchone()

        if cache_row:
            all_books = json.loads(cache_row["results_json"])
        else:
            all_books = await _book_search.get_hc_author_books(hc_author_id, api_key)
            expires_iso = (now_dt + timedelta(days=14)).isoformat()
            await db.execute(
                """INSERT INTO metadata_cache (id, query, source, results_json, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(query, source) DO UPDATE SET
                     results_json = excluded.results_json,
                     created_at = excluded.created_at,
                     expires_at = excluded.expires_at""",
                (str(uuid.uuid4()), hc_author_id, "author_books_rich",
                 json.dumps(all_books), now_iso, expires_iso),
            )
            await db.commit()

        # Owned HC book IDs — any book in the library with a book_formats entry
        owned_rows = await (
            await db.execute(
                """SELECT bl.hardcover_id FROM book_authors ba
                   JOIN book_links bl ON bl.book_id = ba.book_id
                   WHERE ba.author_id = ?
                   AND EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = ba.book_id)""",
                (author_id,),
            )
        ).fetchall()
        owned_hc_ids = {r["hardcover_id"] for r in owned_rows if r["hardcover_id"]}

        candidates = [b for b in all_books if b.get("metadata_id") not in owned_hc_ids]
        candidates = await _annotate_results(candidates, db)

    return {"items": candidates}


@router.get("/authors/{author_id}/books")
async def get_author_books(author_id: str):
    async with get_db() as db:
        author_row = await (
            await db.execute("SELECT id FROM authors WHERE id = ?", (author_id,))
        ).fetchone()
        if not author_row:
            raise HTTPException(status_code=404, detail="Author not found")

        rows = await (
            await db.execute(
                """SELECT b.* FROM books b
                   JOIN book_authors ba ON ba.book_id = b.id
                   WHERE ba.author_id = ?
                   ORDER BY lower(b.title)""",
                (author_id,),
            )
        ).fetchall()

        items = []
        for row in rows:
            book = _book_row_to_dict(row)
            book["authors"] = await _get_book_authors(db, row["id"])
            book["series"] = await _get_book_series(db, row["id"])
            book["link"] = await _get_book_link(db, row["id"])
            book["requests"] = await _get_book_requests(db, row["id"])
            book["formats"] = await _get_book_formats(db, row["id"])
            if book["link"].get("abs_id"):
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}?t={book.get('updated_at','')}"
            items.append(book)

    return items


@router.get("/series")
async def list_series(
    q: str = Query(default=""),
    sort: str = Query(default="name"),
    dir: str = Query(default="asc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unlinked: bool = Query(default=False),
):
    if sort not in {"name", "library_count"}:
        sort = "name"
    if dir not in VALID_DIR:
        dir = "asc"

    order_expr = "lower(s.name)" if sort == "name" else f"library_count {dir}, lower(s.name)"
    order_clause = f"{order_expr} {dir}" if sort == "name" else order_expr

    joins = ""
    conditions = []
    bind: list = []

    if unlinked:
        joins = " JOIN series_links sl ON sl.series_id = s.id"
        conditions.append("(sl.hardcover_series_id IS NULL OR sl.hardcover_series_id = '')")

    if q:
        import unicodedata
        qf = unicodedata.normalize("NFD", q.lower()).encode("ascii", "ignore").decode("ascii")
        like = f"%{qf}%"
        conditions.append("fold(s.name) LIKE ?")
        bind.append(like)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_db() as db:
        count_row = await (
            await db.execute(f"SELECT COUNT(*) FROM series s{joins} {where}", bind)
        ).fetchone()
        rows = await (
            await db.execute(
                f"""SELECT s.*,
                    COUNT(DISTINCT CASE WHEN
                        (s.show_secondary_works = 1 OR bs.position IS NULL OR CAST(bs.position AS REAL) = CAST(CAST(bs.position AS INTEGER) AS REAL))
                        AND EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = bs.book_id)
                    THEN bs.book_id END) as library_count,
                    COUNT(DISTINCT CASE WHEN
                        (s.show_secondary_works = 1 OR bs.position IS NULL OR CAST(bs.position AS REAL) = CAST(CAST(bs.position AS INTEGER) AS REAL))
                        AND NOT EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = bs.book_id)
                        AND EXISTS (SELECT 1 FROM requests r WHERE r.book_id = bs.book_id
                            AND r.status NOT IN ('completed', 'failed'))
                    THEN bs.book_id END) as requested_count
                    FROM series s{joins}
                    LEFT JOIN book_series bs ON bs.series_id = s.id
                    {where}
                    GROUP BY s.id
                    ORDER BY {order_clause}
                    LIMIT ? OFFSET ?""",
                bind + [limit, offset],
            )
        ).fetchall()

        items = []
        for row in rows:
            link_row = await (
                await db.execute(
                    "SELECT hardcover_series_id, hardcover_series_slug FROM series_links WHERE series_id = ?",
                    (row["id"],),
                )
            ).fetchone()
            items.append({
                "id": row["id"],
                "name": row["name"],
                "show_secondary_works": bool(row["show_secondary_works"]),
                "library_count": row["library_count"],
                "requested_count": row["requested_count"],
                "missing_primary": None,
                "upcoming_primary": None,
                "missing_all": None,
                "upcoming_all": None,
                "total_primary": None,
                "link": {
                    "hardcover_series_id": link_row["hardcover_series_id"] if link_row else None,
                    "hardcover_series_slug": link_row["hardcover_series_slug"] if link_row else None,
                },
            })

        # Batch-fetch missing stats from cache for all HC-linked series
        hc_ids = [it["link"]["hardcover_series_id"] for it in items if it["link"]["hardcover_series_id"]]
        if hc_ids:
            now_iso = datetime.now(timezone.utc).isoformat()
            placeholders = ",".join("?" * len(hc_ids))
            stats_rows = await (
                await db.execute(
                    f"SELECT query, results_json FROM metadata_cache WHERE query IN ({placeholders}) AND source = 'series_missing_stats' AND expires_at > ?",
                    hc_ids + [now_iso],
                )
            ).fetchall()
            stats_by_hc_id = {r["query"]: json.loads(r["results_json"]) for r in stats_rows}
            for it in items:
                hc_id = it["link"]["hardcover_series_id"]
                if hc_id and hc_id in stats_by_hc_id:
                    s = stats_by_hc_id[hc_id]
                    it["missing_primary"] = s.get("missing_primary")
                    it["upcoming_primary"] = s.get("upcoming_primary")
                    it["missing_all"] = s.get("missing_all")
                    it["upcoming_all"] = s.get("upcoming_all")
                    it["total_primary"] = s.get("total_primary")

    return {"items": items, "total": count_row[0], "limit": limit, "offset": offset}


@router.get("/series/{series_id}")
async def get_series(series_id: str):
    async with get_db() as db:
        row = await (
            await db.execute("SELECT * FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series not found")
        link_row = await (
            await db.execute(
                "SELECT * FROM series_links WHERE series_id = ?", (series_id,)
            )
        ).fetchone()
        secondary_filter = (
            ""
            if row["show_secondary_works"]
            else "AND (CAST(bs.position AS REAL) = CAST(CAST(bs.position AS INTEGER) AS REAL) OR bs.position IS NULL)"
        )
        counts_row = await (
            await db.execute(
                f"""SELECT
                    COUNT(DISTINCT CASE WHEN EXISTS (
                        SELECT 1 FROM book_formats bf WHERE bf.book_id = bs.book_id
                    ) THEN bs.book_id END) as library_count,
                    COUNT(DISTINCT CASE WHEN NOT EXISTS (
                        SELECT 1 FROM book_formats bf WHERE bf.book_id = bs.book_id
                    ) AND EXISTS (
                        SELECT 1 FROM requests r WHERE r.book_id = bs.book_id
                        AND r.status NOT IN ('completed', 'failed')
                    ) THEN bs.book_id END) as requested_count
                   FROM book_series bs WHERE bs.series_id = ? {secondary_filter}""",
                (series_id,),
            )
        ).fetchone()
    return {
        "id": row["id"],
        "name": row["name"],
        "show_secondary_works": bool(row["show_secondary_works"]),
        "library_count": counts_row["library_count"] if counts_row else 0,
        "requested_count": counts_row["requested_count"] if counts_row else 0,
        "link": {
            "hardcover_series_id": link_row["hardcover_series_id"] if link_row else None,
            "hardcover_series_slug": link_row["hardcover_series_slug"] if link_row else None,
            "abs_series_id": link_row["abs_series_id"] if link_row else None,
        },
    }


class PatchSeriesBody(BaseModel):
    show_secondary_works: Optional[bool] = None


@router.patch("/series/{series_id}")
async def patch_series(series_id: str, body: PatchSeriesBody):
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series not found")
        if body.show_secondary_works is not None:
            await db.execute(
                "UPDATE series SET show_secondary_works = ? WHERE id = ?",
                (1 if body.show_secondary_works else 0, series_id),
            )
        await db.commit()
    return {"ok": True}


@router.get("/series/{series_id}/books")
async def get_series_books(series_id: str):
    async with get_db() as db:
        series_row = await (
            await db.execute("SELECT id FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not series_row:
            raise HTTPException(status_code=404, detail="Series not found")

        rows = await (
            await db.execute(
                """SELECT b.*, bs.position FROM books b
                   JOIN book_series bs ON bs.book_id = b.id
                   WHERE bs.series_id = ?
                   AND EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = b.id)
                   ORDER BY CAST(bs.position AS REAL), bs.position""",
                (series_id,),
            )
        ).fetchall()

        items = []
        for row in rows:
            book = _book_row_to_dict(row)
            book["series_position"] = row["position"]
            book["authors"] = await _get_book_authors(db, row["id"])
            book["series"] = await _get_book_series(db, row["id"])
            book["link"] = await _get_book_link(db, row["id"])
            book["requests"] = await _get_book_requests(db, row["id"])
            book["formats"] = await _get_book_formats(db, row["id"])
            if book["link"].get("abs_id"):
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}?t={book.get('updated_at','')}"
            items.append(book)

    return items


@router.get("/series/{series_id}/missing")
async def get_series_missing(series_id: str):
    """Return missing books for a series, with full metadata per entry."""

    async with get_db() as db:
        series_row = await (
            await db.execute("SELECT id, name, show_secondary_works FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not series_row:
            raise HTTPException(status_code=404, detail="Series not found")
        show_secondary = bool(series_row["show_secondary_works"])

        link_row = await (
            await db.execute(
                "SELECT hardcover_series_id FROM series_links WHERE series_id = ?",
                (series_id,),
            )
        ).fetchone()
        hc_series_id = (link_row["hardcover_series_id"] if link_row else None) or ""

        if not hc_series_id:
            return {"items": [], "error": "Series not linked to Hardcover"}

        settings = await get_settings()
        api_key = settings.get("hardcover", {}).get("api_key", "")
        if not api_key:
            return {"items": [], "error": "Hardcover API key not configured"}

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        # Check cache — stores full normalised book data for all series entries
        cache_row = await (
            await db.execute(
                "SELECT results_json FROM metadata_cache WHERE query = ? AND source = ? AND expires_at > ?",
                (hc_series_id, "series_books_rich", now_iso),
            )
        ).fetchone()

        if cache_row:
            all_books = json.loads(cache_row["results_json"])
        else:
            all_books = await _book_search.get_hc_series_books(hc_series_id, api_key)
            expires_iso = (now_dt + timedelta(days=14)).isoformat()
            await db.execute(
                """INSERT INTO metadata_cache (id, query, source, results_json, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(query, source) DO UPDATE SET
                     results_json = excluded.results_json,
                     created_at = excluded.created_at,
                     expires_at = excluded.expires_at""",
                (str(__import__("uuid").uuid4()), hc_series_id, "series_books_rich",
                 json.dumps(all_books), now_iso, expires_iso),
            )
            await db.commit()

        # Get owned positions and HC book IDs — only books actually in the library (have formats)
        owned_rows = await (
            await db.execute(
                """SELECT bl.hardcover_id
                   FROM book_series bs
                   JOIN books b ON b.id = bs.book_id
                   LEFT JOIN book_links bl ON bl.book_id = b.id
                   WHERE bs.series_id = ?
                   AND EXISTS (SELECT 1 FROM book_formats bf WHERE bf.book_id = b.id)""",
                (series_id,),
            )
        ).fetchall()
        owned_hc_ids = {r["hardcover_id"] for r in owned_rows if r["hardcover_id"]}

        candidates = [
            b for b in all_books
            if not b.get("compilation")
            and b.get("metadata_id") not in owned_hc_ids
        ]

        if not show_secondary:
            candidates = [b for b in candidates if _is_primary_position(b.get("series_position") or "")]

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
        for b in all_books:
            if not b.get("release_date") and b.get("metadata_id") in local_date_map:
                b["release_date"] = local_date_map[b["metadata_id"]]

        # Write missing stats to cache
        from ..services.library_sync import _compute_series_stats
        stats = _compute_series_stats(all_books, owned_hc_ids, show_secondary)
        expires_iso = (now_dt + timedelta(days=14)).isoformat()
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

        # Annotate with live library/request state
        candidates = await _annotate_results(candidates, db)

    return {"items": candidates, "show_secondary_works": show_secondary}


class LinkLibraryBookBody(BaseModel):
    book_id: str
    position: Optional[str] = None


@router.post("/series/{series_id}/link-library-book")
async def link_library_book_to_series(
    series_id: str,
    body: LinkLibraryBookBody,
    auth: dict = Depends(require_admin),
):
    """Add a book already in the library to this series (local DB + ABS metadata patch)."""
    settings = await get_settings()
    api_key = settings.get("hardcover", {}).get("api_key", "")

    async with get_db() as db:
        series_row = await (
            await db.execute("SELECT id, name FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not series_row:
            raise HTTPException(status_code=404, detail="Series not found")

        book_row = await (
            await db.execute("SELECT id, title FROM books WHERE id = ?", (body.book_id,))
        ).fetchone()
        if not book_row:
            raise HTTPException(status_code=404, detail="Book not found")

        fmt_rows = await (
            await db.execute(
                "SELECT abs_id FROM book_formats WHERE book_id = ? AND abs_id IS NOT NULL",
                (body.book_id,),
            )
        ).fetchall()
        if not fmt_rows:
            raise HTTPException(status_code=400, detail="Book is not in the library")

        now = _now()
        await db.execute(
            """INSERT INTO book_series (id, book_id, series_id, position, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(book_id, series_id) DO NOTHING""",
            (str(uuid.uuid4()), body.book_id, series_id, body.position or "", now),
        )
        await db.commit()

        # Rebuild ABS metadata with all series now including the new one
        from ..services.organizer import _build_abs_metadata
        from ..services.audiobookshelf import AudiobookshelfService

        abs_svc = AudiobookshelfService(settings.get("audiobookshelf", {}))
        seen_abs_ids = set()
        for fmt_row in fmt_rows:
            abs_id = fmt_row["abs_id"]
            if abs_id in seen_abs_ids:
                continue
            seen_abs_ids.add(abs_id)
            narrator_row = await (
                await db.execute(
                    "SELECT narrator FROM book_formats WHERE book_id = ? AND abs_id = ?",
                    (body.book_id, abs_id),
                )
            ).fetchone()
            narrator = (narrator_row["narrator"] or "") if narrator_row else ""
            meta = await _build_abs_metadata(db, body.book_id, narrator, api_key)
            ok = await abs_svc.update_item_metadata(abs_id, meta)
            if not ok:
                logger.warning("link-library-book: ABS metadata update failed for item %s", abs_id)

    return {"ok": True}


@router.get("/series/{series_id}/series-downloads")
async def list_series_downloads(series_id: str, auth: dict = Depends(require_admin)):
    """Return active series pack downloads for this series (excludes completed/failed)."""
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id FROM series WHERE id = ?", (series_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series not found")

        rows = await (
            await db.execute(
                """SELECT id, status, type, title, protocol, size, grabbed_at, updated_at, proposed_mappings
                   FROM series_downloads
                   WHERE series_id = ? AND status NOT IN ('completed', 'failed')
                   ORDER BY grabbed_at DESC LIMIT 1""",
                (series_id,),
            )
        ).fetchall()

    return [
        {
            "id": r["id"],
            "status": r["status"],
            "type": r["type"],
            "title": r["title"],
            "protocol": r["protocol"],
            "size": r["size"],
            "grabbed_at": r["grabbed_at"],
            "updated_at": r["updated_at"],
            "proposed_mappings": json.loads(r["proposed_mappings"]) if r["proposed_mappings"] else None,
        }
        for r in rows
    ]


class ConfirmSeriesPackBody(BaseModel):
    mappings: list[dict]


@router.post("/series/{series_id}/series-downloads/{sdl_id}/confirm")
async def confirm_series_pack(
    series_id: str, sdl_id: str, body: ConfirmSeriesPackBody, auth: dict = Depends(require_admin)
):
    """Store confirmed mappings and kick off organise."""
    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT id, status FROM series_downloads WHERE id = ? AND series_id = ?",
                (sdl_id, series_id),
            )
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series download not found")
        if row["status"] != "awaiting_review":
            raise HTTPException(status_code=400, detail=f"Status is {row['status']}, not awaiting_review")

        confirmed = [
            {"filepath": m["filepath"], "book_id": m["book_id"], "action": "place"}
            for m in body.mappings
            if m.get("filepath") and m.get("book_id")
        ]
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE series_downloads SET status='organizing', proposed_mappings=?, updated_at=? WHERE id=?",
            (json.dumps(confirmed), now, sdl_id),
        )
        await db.commit()

    from ..services.organizer import auto_organize_series_pack
    asyncio.create_task(auto_organize_series_pack(sdl_id))
    return {"ok": True}


@router.post("/series/{series_id}/series-downloads/{sdl_id}/rescan")
async def rescan_series_pack(series_id: str, sdl_id: str, auth: dict = Depends(require_admin)):
    """Re-run file→book mapping computation (e.g. after adding a new book/request)."""
    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT id, status FROM series_downloads WHERE id = ? AND series_id = ?",
                (sdl_id, series_id),
            )
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Series download not found")
        if row["status"] != "awaiting_review":
            raise HTTPException(status_code=400, detail=f"Status is {row['status']}, not awaiting_review")
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE series_downloads SET status='rescanning', updated_at=? WHERE id=?",
            (now, sdl_id),
        )
        await db.commit()

    from ..services.organizer import compute_series_pack_mappings
    asyncio.create_task(compute_series_pack_mappings(sdl_id))
    return {"ok": True}


@router.post("/series/{series_id}/search-pack")
async def search_series_pack(series_id: str, auth: dict = Depends(require_admin)):
    """Search Prowlarr for series pack releases."""
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id, name FROM series WHERE id = ?", (series_id,))
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")

    settings = await get_settings()
    prowlarr_settings = settings.get("prowlarr", {})
    if not prowlarr_settings.get("url") or not prowlarr_settings.get("api_key"):
        return {"results": [], "error": "Prowlarr not configured"}

    from ..services.download_clients import prowlarr_search

    series_name = row["name"]
    try:
        raw_results = await prowlarr_search(
            prowlarr_settings, series_name,
            book_type="ebook",
            title=series_name, author="",
        )
    except Exception as e:
        logger.warning("Prowlarr series pack search failed for %s: %s", series_id, e)
        return {"results": [], "error": str(e)}

    results = [
        {
            "protocol": r.get("protocol"),
            "title": r.get("title"),
            "indexer": r.get("indexer"),
            "size": r.get("size"),
            "guid": r.get("guid"),
            "download_url": r.get("downloadUrl"),
            "info_url": r.get("infoUrl"),
            "seeders": r.get("seeders"),
            "leechers": r.get("leechers"),
            "age": r.get("age"),
        }
        for r in raw_results
    ]
    return {"results": results}


class SeriesPackDownloadBody(BaseModel):
    download_url: str
    protocol: str
    indexer: Optional[str] = None
    guid: Optional[str] = None
    title: Optional[str] = None
    info_url: Optional[str] = None
    size: Optional[int] = None
    type: str = "ebook"


@router.post("/series/{series_id}/download-pack")
async def trigger_series_pack_download(
    series_id: str, body: SeriesPackDownloadBody, auth: dict = Depends(require_admin)
):
    """Send a series pack release to the download client and record it."""
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id FROM series WHERE id = ?", (series_id,))
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Series not found")

    settings = await get_settings()

    from ..services.download_clients import QBittorrentClient, SABnzbdClient

    if body.protocol == "torrent":
        client_settings = settings.get("qbittorrent", {})
        if not client_settings.get("url"):
            raise HTTPException(status_code=400, detail="qBittorrent not configured")
        client = QBittorrentClient(client_settings)
        client_name = "qbittorrent"
    elif body.protocol == "usenet":
        client_settings = settings.get("sabnzbd", {})
        if not client_settings.get("url"):
            raise HTTPException(status_code=400, detail="SABnzbd not configured")
        client = SABnzbdClient(client_settings)
        client_name = "sabnzbd"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown protocol: {body.protocol}")

    try:
        download_id = await client.add(body.download_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Download client error: {e}")

    now = datetime.now(timezone.utc).isoformat()
    sdl_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            """INSERT OR IGNORE INTO series_downloads
               (id, series_id, type, title, indexer, guid, info_url, protocol,
                size, download_client, download_id, status, grabbed_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'snatched', ?, ?)""",
            (sdl_id, series_id, body.type, body.title, body.indexer, body.guid,
             body.info_url, body.protocol, body.size, client_name, download_id, now, now),
        )
        await db.commit()

    return {"ok": True, "series_download_id": sdl_id}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_primary_position(pos: str) -> bool:
    """True if the series position is a whole number (primary work)."""
    try:
        n = float(pos)
        return n == int(n)
    except (ValueError, TypeError):
        return False

async def _get_book_authors(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            """SELECT a.id, a.name, ba.author_position,
                      al.abs_author_id, al.hardcover_author_id, al.hardcover_author_slug
               FROM authors a
               JOIN book_authors ba ON ba.author_id = a.id
               LEFT JOIN author_links al ON al.author_id = a.id
               WHERE ba.book_id = ? ORDER BY ba.author_position""",
            (book_id,),
        )
    ).fetchall()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "position": r["author_position"],
            "abs_author_id": r["abs_author_id"],
            "hardcover_author_id": r["hardcover_author_id"],
            "hardcover_author_slug": r["hardcover_author_slug"],
        }
        for r in rows
    ]


async def _get_book_series(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            """SELECT s.id, s.name, bs.position,
                  (SELECT COUNT(*) FROM book_series bs2
                   JOIN book_formats bf ON bf.book_id = bs2.book_id
                   WHERE bs2.series_id = s.id) as library_count
               FROM series s JOIN book_series bs ON bs.series_id = s.id
               WHERE bs.book_id = ?""",
            (book_id,),
        )
    ).fetchall()
    return [{"id": r["id"], "name": r["name"], "position": r["position"],
             "library_count": r["library_count"]} for r in rows]


async def _get_book_link(db, book_id: str) -> dict:
    row = await (
        await db.execute(
            "SELECT abs_id, hardcover_id, hardcover_slug FROM book_links WHERE book_id = ?",
            (book_id,),
        )
    ).fetchone()
    if not row:
        return {"abs_id": None, "hardcover_id": None}
    return {"abs_id": row["abs_id"], "hardcover_id": row["hardcover_id"], "hardcover_slug": row["hardcover_slug"]}


async def _get_book_requests(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            """SELECT r.id, r.type, r.status, r.narrator, r.requested_by_user_id, u.username as requested_by_username
               FROM requests r LEFT JOIN users u ON u.id = r.requested_by_user_id
               WHERE r.book_id = ?
                 AND r.status NOT IN ('rejected')
                 AND NOT EXISTS (
                     SELECT 1 FROM book_formats bf
                     WHERE bf.book_id = r.book_id AND bf.type = r.type
                 )
               ORDER BY r.created_at""",
            (book_id,),
        )
    ).fetchall()
    return [{"id": r["id"], "type": r["type"], "status": r["status"], "narrator": r["narrator"],
             "requested_by_user_id": r["requested_by_user_id"], "requested_by_username": r["requested_by_username"]} for r in rows]


async def _get_book_formats(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            """SELECT id, type, narrator, abs_id, abs_url, fulfilled_by_request_id
               FROM book_formats WHERE book_id = ? ORDER BY type""",
            (book_id,),
        )
    ).fetchall()
    settings = await get_settings()
    abs_cfg = settings.get("audiobookshelf", {})
    public_url = abs_cfg.get("url", "").rstrip("/")
    result = []
    for r in rows:
        abs_url = r["abs_url"]
        if r["abs_id"] and public_url:
            abs_url = f"{public_url}/item/{r['abs_id']}"
        result.append({"id": r["id"], "type": r["type"], "narrator": r["narrator"],
                       "abs_id": r["abs_id"], "abs_url": abs_url,
                       "fulfilled_by_request_id": r["fulfilled_by_request_id"]})
    return result


# ── Search annotation helper ───────────────────────────────────────────────────

async def _annotate_results(results: list[dict], db) -> list[dict]:
    """Annotate search results with local DB data (in_library, book_id, library_formats, existing_requests, series IDs)."""
    for result in results:
        hc_id = result.get("metadata_id")
        if not hc_id:
            continue

        link_row = await (
            await db.execute(
                "SELECT book_id FROM book_links WHERE hardcover_id = ?", (hc_id,)
            )
        ).fetchone()
        if not link_row:
            continue

        book_id = link_row["book_id"]
        result["book_id"] = book_id

        book_row = await (
            await db.execute(
                "SELECT release_date, release_date_fetched FROM books WHERE id = ?", (book_id,)
            )
        ).fetchone()
        if book_row:
            result["release_date"] = book_row["release_date"] or ""
            result["release_date_fetched"] = bool(book_row["release_date_fetched"])

        fmt_rows = await (
            await db.execute(
                "SELECT type, narrator FROM book_formats WHERE book_id = ?",
                (book_id,),
            )
        ).fetchall()
        result["in_library"] = len(fmt_rows) > 0
        result["library_formats"] = [
            {"type": r["type"], "narrator": r["narrator"]} for r in fmt_rows
        ]

        req_rows = await (
            await db.execute(
                "SELECT id, type, status, narrator, requested_by_user_id FROM requests WHERE book_id = ? AND status NOT IN ('failed', 'rejected') ORDER BY created_at",
                (book_id,),
            )
        ).fetchall()
        result["existing_requests"] = [
            {"id": r["id"], "type": r["type"], "status": r["status"], "narrator": r["narrator"], "requested_by_user_id": r["requested_by_user_id"]}
            for r in req_rows
        ]

        # Resolve local series UUIDs
        for s in result.get("series", []):
            hc_sid = s.get("hardcover_series_id")
            if hc_sid:
                sl_row = await (
                    await db.execute(
                        "SELECT series_id FROM series_links WHERE hardcover_series_id = ?",
                        (hc_sid,),
                    )
                ).fetchone()
                if sl_row:
                    s["id"] = sl_row["series_id"]

    return results


# ── Search endpoints ───────────────────────────────────────────────────────────

@router.get("/search/metadata")
async def search_metadata(
    q: str = Query(default=""),
    series_id: str = Query(default=""),
):
    if not q.strip():
        return {"results": []}

    settings = await get_settings()
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"results": [], "error": "Hardcover API key not configured"}

    # Resolve local series_id to HC series ID for context sorting
    context_hc_series_id = ""
    if series_id:
        async with get_db() as db:
            sl_row = await (
                await db.execute(
                    "SELECT hardcover_series_id FROM series_links WHERE series_id = ?",
                    (series_id,),
                )
            ).fetchone()
        if sl_row:
            context_hc_series_id = sl_row["hardcover_series_id"] or ""

    from ..services.book_search import search_books
    results = await search_books(q.strip(), api_key, context_hc_series_id=context_hc_series_id)

    async with get_db() as db:
        results = await _annotate_results(results, db)

    return {"results": results}


@router.get("/search/advanced")
async def search_advanced(
    title: str = Query(default=""),
    author: str = Query(default=""),
    series: str = Query(default=""),
    series_id: str = Query(default=""),
    author_id: str = Query(default=""),
    hc_series_id: str = Query(default=""),
):
    settings = await get_settings()
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"results": [], "error": "Hardcover API key not configured"}

    if author_id:
        from ..services.book_search import get_hc_author_books
        results = await get_hc_author_books(author_id, api_key)
        async with get_db() as db:
            results = await _annotate_results(results, db)
        return {"results": results}

    if hc_series_id:
        from ..services.book_search import get_hc_series_books
        results = await get_hc_series_books(hc_series_id, api_key)
        async with get_db() as db:
            results = await _annotate_results(results, db)
        return {"results": results}

    if not title.strip() and not author.strip() and not series.strip():
        return {"results": []}

    context_hc_series_id = ""
    if series_id:
        async with get_db() as db:
            sl_row = await (
                await db.execute(
                    "SELECT hardcover_series_id FROM series_links WHERE series_id = ?",
                    (series_id,),
                )
            ).fetchone()
        if sl_row:
            context_hc_series_id = sl_row["hardcover_series_id"] or ""

    from ..services.book_search import advanced_search_books
    results = await advanced_search_books(
        title=title, author=author, series=series,
        api_key=api_key, context_hc_series_id=context_hc_series_id,
    )

    async with get_db() as db:
        results = await _annotate_results(results, db)

    return {"results": results}


# ── POST /api/books ────────────────────────────────────────────────────────────

class BookRequestItem(BaseModel):
    type: str
    narrator: Optional[str] = None


class SeriesItem(BaseModel):
    name: str
    position: Optional[str] = None
    hardcover_id: Optional[str] = None


class CreateBookBody(BaseModel):
    title: str
    author: str = ""
    cover_url: Optional[str] = None
    series_list: list[SeriesItem] = []
    metadata_source: Optional[str] = None
    metadata_id: Optional[str] = None
    metadata_url: Optional[str] = None
    hardcover_slug: Optional[str] = None
    requests: list[BookRequestItem] = []


@router.post("/books")
async def create_book(body: CreateBookBody, auth: dict = Depends(require_auth)):
    """Create a book (if it doesn't already exist) and attach requests."""
    from ..routes.requests import _create_request
    from ..services.library_sync import _get_or_create_author, _get_or_create_series, _split_authors

    async with get_db() as db:
        book_id = None

        # 1. Check by hardcover_id first (most reliable dedup)
        if body.metadata_id:
            link_row = await (
                await db.execute(
                    "SELECT book_id FROM book_links WHERE hardcover_id = ?",
                    (body.metadata_id,),
                )
            ).fetchone()
            if link_row:
                book_id = link_row["book_id"]

        # 2. Fall back to title + primary author match
        if not book_id and body.title:
            title_match = await (
                await db.execute(
                    "SELECT b.id FROM books b WHERE lower(b.title) = lower(?)",
                    (body.title.strip(),),
                )
            ).fetchone()
            if title_match:
                book_id = title_match["id"]

        # 3. Create new book
        now = _now()
        book_is_new = not book_id
        if not book_id:
            book_id = str(uuid.uuid4())
            await db.execute(
                """INSERT INTO books (id, title, cover_url, metadata_source, metadata_url, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    book_id,
                    body.title.strip(),
                    body.cover_url or None,
                    body.metadata_source or "hardcover",
                    body.metadata_url or None,
                    now, now,
                ),
            )
            # book_links row (only on creation — sync owns this for ABS-linked books)
            await db.execute(
                "INSERT OR IGNORE INTO book_links (id, book_id, hardcover_id, hardcover_slug, linked_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), book_id, body.metadata_id or None, body.hardcover_slug or None, now),
            )

        # Backfill slug if we have one and it's not already set
        if body.hardcover_slug:
            await db.execute(
                "UPDATE book_links SET hardcover_slug = ? WHERE book_id = ? AND (hardcover_slug IS NULL OR hardcover_slug = '')",
                (body.hardcover_slug, book_id),
            )

        # Authors — always upsert so existing books without authors get filled in
        author_names = _split_authors(body.author) if body.author else []
        for pos, name in enumerate(author_names, 1):
            author_id = await _get_or_create_author(db, name)
            await db.execute(
                "INSERT OR IGNORE INTO book_authors (id, book_id, author_id, author_position, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), book_id, author_id, pos, now),
            )

        # Series — upsert all entries
        if body.series_list:
            from ..services.library_sync import _set_hc_series_id
            for s in body.series_list:
                if not s.name:
                    continue
                hc_sid = str(s.hardcover_id) if s.hardcover_id else ""
                series_id = await _get_or_create_series(db, s.name.strip(), hc_series_id=hc_sid)
                await db.execute(
                    "INSERT OR IGNORE INTO book_series (id, book_id, series_id, position, created_at) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), book_id, series_id, s.position or None, now),
                )
                if hc_sid:
                    await _set_hc_series_id(db, series_id, hc_sid)

        # 4. Create requests
        created = 0
        skipped = 0
        for req in body.requests:
            if req.type not in ("audiobook", "ebook"):
                continue
            result = await _create_request(db, book_id, req.type, req.narrator or None, user_id=auth["user_id"], role=auth["role"])
            if result:
                created += 1
            else:
                skipped += 1

        await db.commit()

    # Fetch release_date and slug from HC for new books, or existing books not yet fetched
    if body.metadata_id and book_is_new:
        from ..services.library_sync import _fetch_hc_book_meta
        from ..settings import get_settings
        settings = await get_settings()
        api_key = settings.get("hardcover", {}).get("api_key", "")
        if api_key:
            try:
                meta = await _fetch_hc_book_meta(int(body.metadata_id), api_key)
                if meta:
                    async with get_db() as db:
                        if meta.get("release_date"):
                            await db.execute(
                                "UPDATE books SET release_date = ?, release_date_fetched = 1 WHERE id = ?",
                                (meta["release_date"], book_id),
                            )
                        else:
                            await db.execute(
                                "UPDATE books SET release_date_fetched = 1 WHERE id = ?",
                                (book_id,),
                            )
                        if meta.get("slug"):
                            await db.execute(
                                "UPDATE book_links SET hardcover_slug = ? WHERE book_id = ? AND (hardcover_slug IS NULL OR hardcover_slug = '')",
                                (meta["slug"], book_id),
                            )
                        await db.commit()
            except Exception:
                pass  # non-fatal; cache_refresh will backfill

    async with get_db() as db:
        # Return the book record
        book_row = await (
            await db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        ).fetchone()
        book = _book_row_to_dict(book_row)
        book["authors"] = await _get_book_authors(db, book_id)
        book["series"] = await _get_book_series(db, book_id)
        book["link"] = await _get_book_link(db, book_id)
        book["requests"] = await _get_book_requests(db, book_id)
        book["formats"] = await _get_book_formats(db, book_id)

    book["_created_requests"] = created
    book["_skipped_requests"] = skipped
    return book
