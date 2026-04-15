"""GET /api/downloads — live active downloads with progress from clients."""
import asyncio
import logging

from fastapi import APIRouter

from ..database import get_db
from ..settings import get_settings

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/downloads")
async def list_downloads():
    """Return active downloads (snatched/downloading) with live progress."""
    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT d.id, d.request_id, d.title, d.indexer, d.protocol,
                          d.size, d.status, d.download_client, d.download_id,
                          d.download_path, d.grabbed_at,
                          r.type, r.narrator, r.status as req_status,
                          b.title as book_title,
                          (SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                           WHERE ba.book_id = r.book_id ORDER BY ba.author_position LIMIT 1) as author
                   FROM downloads d
                   JOIN requests r ON r.id = d.request_id
                   JOIN books b ON b.id = r.book_id
                   WHERE r.status IN ('snatched', 'downloading')
                   ORDER BY d.grabbed_at DESC"""
            )
        ).fetchall()

    if not rows:
        return {"items": [], "client_unreachable": False}

    settings = await get_settings()
    qbit_settings = settings.get("qbittorrent", {})
    sab_settings = settings.get("sabnzbd", {})

    from ..services.download_clients import QBittorrentClient, SABnzbdClient

    # Build one client per protocol (reused across rows)
    qbit = QBittorrentClient(qbit_settings) if qbit_settings.get("url") else None
    sab = SABnzbdClient(sab_settings) if sab_settings.get("url") else None

    client_unreachable = False
    items = []

    async def _live_progress(row) -> dict:
        nonlocal client_unreachable
        base = {
            "id": row["id"],
            "request_id": row["request_id"],
            "book_title": row["book_title"],
            "author": row["author"],
            "type": row["type"],
            "narrator": row["narrator"],
            "protocol": row["protocol"],
            "indexer": row["indexer"],
            "release_title": row["title"],
            "size": row["size"],
            "status": row["req_status"],
            "grabbed_at": row["grabbed_at"],
            "progress": None,
            "eta": None,
            "speed": None,
        }
        if not row["download_id"]:
            return base
        try:
            if row["download_client"] == "qbittorrent" and qbit:
                info = await asyncio.wait_for(qbit.check(row["download_id"]), timeout=5.0)
            elif row["download_client"] == "sabnzbd" and sab:
                info = await asyncio.wait_for(sab.check(row["download_id"]), timeout=5.0)
            else:
                return base
            base.update({
                "progress": round(info.get("progress", 0) * 100, 1),
                "eta": info.get("eta"),
                "speed": info.get("speed"),
            })
        except Exception as e:
            logger.warning("live progress fetch failed: %s", e)
            client_unreachable = True
        return base

    tasks = [_live_progress(row) for row in rows]
    items = await asyncio.gather(*tasks)

    return {"items": list(items), "client_unreachable": client_unreachable}
