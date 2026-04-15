import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import get_db
from ..settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Shared helper ──────────────────────────────────────────────────────────────

async def _create_request(db, book_id: str, req_type: str, narrator: str = None) -> dict | None:
    """Create a request row, returning None (skipped) if a dedup rule blocks it.

    Dedup rules:
    - An active (non-failed, non-completed) request for same book + type already exists.
    - A book_formats row for same book + type + same narrator (case-insensitive) exists.
    """
    active = await (
        await db.execute(
            """SELECT id FROM requests
               WHERE book_id = ? AND type = ? AND status NOT IN ('failed', 'completed')""",
            (book_id, req_type),
        )
    ).fetchone()
    if active:
        return None

    narrator_norm = narrator or ''
    in_lib = await (
        await db.execute(
            """SELECT id FROM book_formats
               WHERE book_id = ? AND type = ? AND lower(narrator) = lower(?)""",
            (book_id, req_type, narrator_norm),
        )
    ).fetchone()
    if in_lib:
        return None

    req_id = str(uuid.uuid4())
    now = _now()
    await db.execute(
        """INSERT INTO requests (id, book_id, type, status, narrator, created_at, updated_at)
           VALUES (?, ?, ?, 'requested', ?, ?, ?)""",
        (req_id, book_id, req_type, narrator, now, now),
    )
    return {
        "id": req_id,
        "book_id": book_id,
        "type": req_type,
        "status": "requested",
        "narrator": narrator,
        "created_at": now,
        "updated_at": now,
    }


# ── Request detail helper ──────────────────────────────────────────────────────

async def _request_detail(db, req_id: str) -> dict:
    row = await (
        await db.execute(
            """SELECT r.*, b.title as book_title,
                      (SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                       WHERE ba.book_id = r.book_id ORDER BY ba.author_position LIMIT 1) as author
               FROM requests r JOIN books b ON b.id = r.book_id
               WHERE r.id = ?""",
            (req_id,),
        )
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "book_id": row["book_id"],
        "book_title": row["book_title"],
        "author": row["author"],
        "type": row["type"],
        "status": row["status"],
        "narrator": row["narrator"],
        "isbn": row["isbn"],
        "asin": row["asin"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_searched_at": row["last_searched_at"],
        "search_count": row["search_count"],
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

class CreateRequestBody(BaseModel):
    book_id: str
    type: str
    narrator: Optional[str] = None


@router.post("/requests")
async def create_request(body: CreateRequestBody):
    if body.type not in ("audiobook", "ebook"):
        raise HTTPException(status_code=400, detail="type must be audiobook or ebook")
    async with get_db() as db:
        book = await (
            await db.execute("SELECT id FROM books WHERE id = ?", (body.book_id,))
        ).fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        req = await _create_request(db, body.book_id, body.type, body.narrator or '')
        if req is None:
            return {"skipped": True}
        await db.commit()
        detail = await _request_detail(db, req["id"])
    return detail


@router.get("/requests")
async def list_requests(
    status: str = Query(default=""),
    type: str = Query(default=""),
    book_id: str = Query(default=""),
    q: str = Query(default=""),
    sort: str = Query(default="created_at"),
    dir: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    valid_sorts = {"created_at", "status", "book_title", "type"}
    if sort not in valid_sorts:
        sort = "created_at"
    if dir not in ("asc", "desc"):
        dir = "desc"

    sort_expr = {
        "created_at": "r.created_at",
        "status": "r.status",
        "book_title": "lower(b.title)",
        "type": "r.type",
    }[sort]

    conditions = ["r.status != 'in_library'"]
    bind: list = []

    if status:
        conditions = ["r.status = ?"]
        bind.append(status)
    if type:
        conditions.append("r.type = ?")
        bind.append(type)
    if book_id:
        conditions.append("r.book_id = ?")
        bind.append(book_id)
    if q:
        like = f"%{q}%"
        conditions.append(
            "(b.title LIKE ? OR EXISTS ("
            "SELECT 1 FROM authors a JOIN book_authors ba ON ba.author_id = a.id "
            "WHERE ba.book_id = r.book_id AND a.name LIKE ?))"
        )
        bind.extend([like, like])

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_sql = (
        "FROM requests r JOIN books b ON b.id = r.book_id "
        "LEFT JOIN book_authors ba2 ON ba2.book_id = r.book_id AND ba2.author_position = 1 "
        "LEFT JOIN authors a2 ON a2.id = ba2.author_id "
        f"{where}"
    )

    async with get_db() as db:
        count_row = await (
            await db.execute(f"SELECT COUNT(*) {base_sql}", bind)
        ).fetchone()
        rows = await (
            await db.execute(
                f"""SELECT r.*, b.title as book_title, b.release_date as release_date, a2.name as author
                    {base_sql}
                    ORDER BY {sort_expr} {dir}
                    LIMIT ? OFFSET ?""",
                bind + [limit, offset],
            )
        ).fetchall()

    items = [
        {
            "id": r["id"],
            "book_id": r["book_id"],
            "book_title": r["book_title"],
            "author": r["author"],
            "type": r["type"],
            "status": r["status"],
            "narrator": r["narrator"],
            "release_date": r["release_date"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]
    return {"items": items, "total": count_row[0], "limit": limit, "offset": offset}


@router.get("/requests/{request_id}")
async def get_request(request_id: str):
    async with get_db() as db:
        detail = await _request_detail(db, request_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Request not found")
    return detail


@router.delete("/requests/{request_id}")
async def delete_request(request_id: str):
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id FROM requests WHERE id = ?", (request_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        await db.execute("DELETE FROM requests WHERE id = ?", (request_id,))
        await db.commit()
    return {"ok": True}


@router.post("/requests/sync-library")
async def sync_library_requests():
    """Check ABS for active requests and fulfil any found there."""
    settings = await get_settings()
    abs_settings = settings.get("audiobookshelf", {})
    if not abs_settings.get("url"):
        return {"ok": True, "updated": 0}

    from ..services.audiobookshelf import AudiobookshelfService
    abs_svc = AudiobookshelfService(abs_settings)

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT r.id, r.book_id, r.type, r.narrator, b.title,
                          (SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                           WHERE ba.book_id = r.book_id ORDER BY ba.author_position LIMIT 1) as author
                   FROM requests r JOIN books b ON b.id = r.book_id
                   WHERE r.status NOT IN ('completed', 'failed')"""
            )
        ).fetchall()

    updated = 0
    for row in rows:
        try:
            matches = await abs_svc.check_library(row["title"], row["author"] or "")
        except Exception:
            continue
        for item in matches:
            for fmt in item.get("formats", []):
                if fmt.get("type") == row["type"]:
                    now = _now()
                    async with get_db() as db:
                        await db.execute(
                            """INSERT OR IGNORE INTO book_formats
                                   (id, book_id, type, narrator, abs_id, abs_url, fulfilled_by_request_id, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (str(uuid.uuid4()), row["book_id"], row["type"],
                             fmt.get("narrator") or row["narrator"] or '',
                             item.get("abs_id"), item.get("abs_url"),
                             row["id"], now, now),
                        )
                        await db.execute(
                            "UPDATE requests SET status='completed', updated_at=? WHERE id=?",
                            (now, row["id"]),
                        )
                        await db.commit()
                    updated += 1
                    break
            else:
                continue
            break

    return {"ok": True, "updated": updated}


@router.get("/requests/{request_id}/downloads")
async def get_request_downloads(request_id: str):
    async with get_db() as db:
        rows = await (
            await db.execute(
                "SELECT * FROM downloads WHERE request_id = ? ORDER BY grabbed_at DESC",
                (request_id,),
            )
        ).fetchall()
    return [
        {
            "id": r["id"],
            "request_id": r["request_id"],
            "title": r["title"],
            "indexer": r["indexer"],
            "protocol": r["protocol"],
            "size": r["size"],
            "status": r["status"],
            "download_path": r["download_path"],
            "grabbed_at": r["grabbed_at"],
        }
        for r in rows
    ]


@router.post("/requests/{request_id}/search-indexers")
async def search_indexers(request_id: str):
    """Search Prowlarr for releases matching this request."""
    async with get_db() as db:
        row = await (
            await db.execute(
                """SELECT r.type, r.narrator, b.title,
                          (SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                           WHERE ba.book_id = r.book_id ORDER BY ba.author_position LIMIT 1) as author
                   FROM requests r JOIN books b ON b.id = r.book_id
                   WHERE r.id = ?""",
                (request_id,),
            )
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")

    settings = await get_settings()
    prowlarr_settings = settings.get("prowlarr", {})
    if not prowlarr_settings.get("url") or not prowlarr_settings.get("api_key"):
        return {"results": [], "error": "Prowlarr not configured"}

    from ..services.download_clients import prowlarr_search

    query = row["title"]
    if row["author"]:
        query = f"{query} {row['author']}"

    try:
        raw_results = await prowlarr_search(prowlarr_settings, query, book_type=row["type"])
    except Exception as e:
        logger.warning("Prowlarr search failed: %s", e)
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


class DownloadBody(BaseModel):
    download_url: str
    protocol: str
    indexer: Optional[str] = None
    guid: Optional[str] = None
    title: Optional[str] = None
    info_url: Optional[str] = None
    size: Optional[int] = None


@router.post("/requests/{request_id}/download")
async def trigger_download(request_id: str, body: DownloadBody):
    """Send a release to the appropriate download client and record it."""
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id, status FROM requests WHERE id = ?", (request_id,))
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")

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

    now = _now()
    dl_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            """INSERT INTO downloads
               (id, request_id, title, indexer, guid, info_url, protocol,
                size, download_client, download_id, status, grabbed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'snatched', ?)""",
            (dl_id, request_id, body.title, body.indexer, body.guid,
             body.info_url, body.protocol, body.size, client_name, download_id, now),
        )
        await db.execute(
            "UPDATE requests SET status='snatched', updated_at=? WHERE id=?",
            (now, request_id),
        )
        await db.commit()

    return {"ok": True, "download_id": dl_id}


class OrganizeBody(BaseModel):
    path: Optional[str] = None


@router.post("/requests/{request_id}/organize")
async def organize_request(request_id: str, body: OrganizeBody = OrganizeBody()):
    """Manually trigger organize pipeline for a request."""
    async with get_db() as db:
        row = await (
            await db.execute("SELECT id, status FROM requests WHERE id = ?", (request_id,))
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")

        # If a path override is provided, update the most recent downloads record
        if body.path:
            dl_row = await (
                await db.execute(
                    "SELECT id FROM downloads WHERE request_id = ? ORDER BY grabbed_at DESC LIMIT 1",
                    (request_id,),
                )
            ).fetchone()
            if dl_row:
                await db.execute(
                    "UPDATE downloads SET download_path=? WHERE id=?",
                    (body.path, dl_row["id"]),
                )
                await db.commit()

    import asyncio as _asyncio
    from ..services.organizer import auto_organize
    _asyncio.create_task(auto_organize(request_id))
    return {"ok": True}
