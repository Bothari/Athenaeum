import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import get_db
from ..settings import get_settings

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
        like = f"%{q}%"
        conditions.append(
            "(b.title LIKE ? OR EXISTS ("
            "SELECT 1 FROM authors a JOIN book_authors ba ON ba.author_id = a.id "
            "WHERE ba.book_id = b.id AND a.name LIKE ?))"
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
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}"
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
            book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}"
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
        like = f"%{q}%"
        conditions.append("a.name LIKE ?")
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
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}"
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
    if sort not in {"name", "book_count"}:
        sort = "name"
    if dir not in VALID_DIR:
        dir = "asc"

    order_expr = "lower(s.name)" if sort == "name" else f"book_count {dir}, lower(s.name)"
    order_clause = f"{order_expr} {dir}" if sort == "name" else order_expr

    joins = ""
    conditions = []
    bind: list = []

    if unlinked:
        joins = " JOIN series_links sl ON sl.series_id = s.id"
        conditions.append("(sl.hardcover_series_id IS NULL OR sl.hardcover_series_id = '')")

    if q:
        like = f"%{q}%"
        conditions.append("s.name LIKE ?")
        bind.append(like)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with get_db() as db:
        count_row = await (
            await db.execute(f"SELECT COUNT(*) FROM series s{joins} {where}", bind)
        ).fetchone()
        rows = await (
            await db.execute(
                f"""SELECT s.*, COUNT(bs.book_id) as book_count
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
                "book_count": row["book_count"],
                "link": {
                    "hardcover_series_id": link_row["hardcover_series_id"] if link_row else None,
                    "hardcover_series_slug": link_row["hardcover_series_slug"] if link_row else None,
                },
            })

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
    return {
        "id": row["id"],
        "name": row["name"],
        "link": {
            "hardcover_series_id": link_row["hardcover_series_id"] if link_row else None,
            "hardcover_series_slug": link_row["hardcover_series_slug"] if link_row else None,
            "abs_series_id": link_row["abs_series_id"] if link_row else None,
        },
    }


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
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}"
            items.append(book)

    return items


# ── Helpers ────────────────────────────────────────────────────────────────────

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
            """SELECT s.id, s.name, bs.position
               FROM series s JOIN book_series bs ON bs.series_id = s.id
               WHERE bs.book_id = ?""",
            (book_id,),
        )
    ).fetchall()
    return [{"id": r["id"], "name": r["name"], "position": r["position"]} for r in rows]


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
            "SELECT id, type, status, narrator FROM requests WHERE book_id = ? AND status NOT IN ('completed', 'failed') ORDER BY created_at",
            (book_id,),
        )
    ).fetchall()
    return [{"id": r["id"], "type": r["type"], "status": r["status"], "narrator": r["narrator"]} for r in rows]


async def _get_book_formats(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            "SELECT type, narrator FROM book_formats WHERE book_id = ? ORDER BY type",
            (book_id,),
        )
    ).fetchall()
    return [{"type": r["type"], "narrator": r["narrator"]} for r in rows]


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
                "SELECT id, type, status, narrator FROM requests WHERE book_id = ? AND status NOT IN ('completed', 'failed') ORDER BY created_at",
                (book_id,),
            )
        ).fetchall()
        result["existing_requests"] = [
            {"id": r["id"], "type": r["type"], "status": r["status"], "narrator": r["narrator"]}
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
):
    if not title.strip() and not author.strip() and not series.strip():
        return {"results": []}

    settings = await get_settings()
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"results": [], "error": "Hardcover API key not configured"}

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


class CreateBookBody(BaseModel):
    title: str
    author: str = ""
    cover_url: Optional[str] = None
    series: Optional[str] = None
    series_position: Optional[str] = None
    metadata_source: Optional[str] = None
    metadata_id: Optional[str] = None
    metadata_url: Optional[str] = None
    requests: list[BookRequestItem] = []


@router.post("/books")
async def create_book(body: CreateBookBody):
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
        if not book_id:
            book_id = str(uuid.uuid4())
            now = _now()
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

            # Authors
            author_names = _split_authors(body.author) if body.author else []
            for pos, name in enumerate(author_names, 1):
                author_id = await _get_or_create_author(db, name)
                await db.execute(
                    "INSERT OR IGNORE INTO book_authors (book_id, author_id, author_position) VALUES (?, ?, ?)",
                    (book_id, author_id, pos),
                )

            # Series
            if body.series:
                series_id = await _get_or_create_series(db, body.series.strip())
                await db.execute(
                    "INSERT OR IGNORE INTO book_series (book_id, series_id, position) VALUES (?, ?, ?)",
                    (book_id, series_id, body.series_position or None),
                )

            # book_links row
            await db.execute(
                "INSERT OR IGNORE INTO book_links (id, book_id, hardcover_id, linked_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), book_id, body.metadata_id or None, _now()),
            )

        # 4. Create requests
        created = 0
        skipped = 0
        for req in body.requests:
            if req.type not in ("audiobook", "ebook"):
                continue
            result = await _create_request(db, book_id, req.type, req.narrator or None)
            if result:
                created += 1
            else:
                skipped += 1

        await db.commit()

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
