from fastapi import APIRouter, HTTPException, Query

from ..database import get_db

router = APIRouter(prefix="/api")

VALID_BOOK_SORTS = {"title", "author", "created_at"}
VALID_DIR = {"asc", "desc"}


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
):
    if sort not in VALID_BOOK_SORTS:
        sort = "title"
    if dir not in VALID_DIR:
        dir = "asc"

    # Map "author" sort to the first author name via subquery
    if sort == "author":
        order_expr = "(SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id WHERE ba.book_id = b.id ORDER BY ba.author_position LIMIT 1)"
    elif sort == "title":
        order_expr = "lower(b.title)"
    else:
        order_expr = f"b.{sort}"

    async with get_db() as db:
        if q:
            like = f"%{q}%"
            count_row = await (
                await db.execute(
                    """SELECT COUNT(*) FROM books b
                       WHERE b.title LIKE ? OR EXISTS (
                         SELECT 1 FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                         WHERE ba.book_id = b.id AND a.name LIKE ?
                       )""",
                    (like, like),
                )
            ).fetchone()
            rows = await (
                await db.execute(
                    f"""SELECT b.* FROM books b
                       WHERE b.title LIKE ? OR EXISTS (
                         SELECT 1 FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                         WHERE ba.book_id = b.id AND a.name LIKE ?
                       )
                       ORDER BY {order_expr} {dir}
                       LIMIT ? OFFSET ?""",
                    (like, like, limit, offset),
                )
            ).fetchall()
        else:
            count_row = await (
                await db.execute("SELECT COUNT(*) FROM books b")
            ).fetchone()
            rows = await (
                await db.execute(
                    f"SELECT b.* FROM books b ORDER BY {order_expr} {dir} LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            ).fetchall()

        items = []
        for row in rows:
            book = _book_row_to_dict(row)
            book["authors"] = await _get_book_authors(db, row["id"])
            book["series"] = await _get_book_series(db, row["id"])
            book["link"] = await _get_book_link(db, row["id"])
            book["requests"] = await _get_book_requests(db, row["id"])
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
):
    if sort not in {"name", "book_count"}:
        sort = "name"
    if dir not in VALID_DIR:
        dir = "asc"

    order_expr = "lower(a.name)" if sort == "name" else f"book_count {dir}, lower(a.name)"
    order_clause = f"{order_expr} {dir}" if sort == "name" else order_expr

    async with get_db() as db:
        if q:
            like = f"%{q}%"
            count_row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM authors a WHERE a.name LIKE ?", (like,)
                )
            ).fetchone()
            rows = await (
                await db.execute(
                    f"""SELECT a.*, COUNT(ba.book_id) as book_count
                        FROM authors a
                        LEFT JOIN book_authors ba ON ba.author_id = a.id
                        WHERE a.name LIKE ?
                        GROUP BY a.id
                        ORDER BY {order_clause}
                        LIMIT ? OFFSET ?""",
                    (like, limit, offset),
                )
            ).fetchall()
        else:
            count_row = await (
                await db.execute("SELECT COUNT(*) FROM authors a")
            ).fetchone()
            rows = await (
                await db.execute(
                    f"""SELECT a.*, COUNT(ba.book_id) as book_count
                        FROM authors a
                        LEFT JOIN book_authors ba ON ba.author_id = a.id
                        GROUP BY a.id
                        ORDER BY {order_clause}
                        LIMIT ? OFFSET ?""",
                    (limit, offset),
                )
            ).fetchall()

        items = []
        for row in rows:
            link_row = await (
                await db.execute(
                    "SELECT hardcover_author_id FROM author_links WHERE author_id = ?",
                    (row["id"],),
                )
            ).fetchone()
            items.append({
                "id": row["id"],
                "name": row["name"],
                "book_count": row["book_count"],
                "link": {"hardcover_author_id": link_row["hardcover_author_id"] if link_row else None},
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
):
    if sort not in {"name", "book_count"}:
        sort = "name"
    if dir not in VALID_DIR:
        dir = "asc"

    order_expr = "lower(s.name)" if sort == "name" else f"book_count {dir}, lower(s.name)"
    order_clause = f"{order_expr} {dir}" if sort == "name" else order_expr

    async with get_db() as db:
        if q:
            like = f"%{q}%"
            count_row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM series s WHERE s.name LIKE ?", (like,)
                )
            ).fetchone()
            rows = await (
                await db.execute(
                    f"""SELECT s.*, COUNT(bs.book_id) as book_count
                        FROM series s
                        LEFT JOIN book_series bs ON bs.series_id = s.id
                        WHERE s.name LIKE ?
                        GROUP BY s.id
                        ORDER BY {order_clause}
                        LIMIT ? OFFSET ?""",
                    (like, limit, offset),
                )
            ).fetchall()
        else:
            count_row = await (
                await db.execute("SELECT COUNT(*) FROM series s")
            ).fetchone()
            rows = await (
                await db.execute(
                    f"""SELECT s.*, COUNT(bs.book_id) as book_count
                        FROM series s
                        LEFT JOIN book_series bs ON bs.series_id = s.id
                        GROUP BY s.id
                        ORDER BY {order_clause}
                        LIMIT ? OFFSET ?""",
                    (limit, offset),
                )
            ).fetchall()

        items = []
        for row in rows:
            link_row = await (
                await db.execute(
                    "SELECT hardcover_series_id FROM series_links WHERE series_id = ?",
                    (row["id"],),
                )
            ).fetchone()
            items.append({
                "id": row["id"],
                "name": row["name"],
                "book_count": row["book_count"],
                "link": {"hardcover_series_id": link_row["hardcover_series_id"] if link_row else None},
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
            if book["link"].get("abs_id"):
                book["cover_url"] = f"/api/abs/cover/{book['link']['abs_id']}"
            items.append(book)

    return items


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_book_authors(db, book_id: str) -> list:
    rows = await (
        await db.execute(
            """SELECT a.id, a.name, ba.author_position,
                      al.abs_author_id, al.hardcover_author_id
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
            "SELECT id, type, status, narrator FROM requests WHERE book_id = ? ORDER BY created_at",
            (book_id,),
        )
    ).fetchall()
    return [{"id": r["id"], "type": r["type"], "status": r["status"], "narrator": r["narrator"]} for r in rows]
