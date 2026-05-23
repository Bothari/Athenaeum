import asyncio
import logging
from datetime import datetime

from croniter import croniter
from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .auth import ensure_session_secret, require_admin, require_auth
from .database import get_db, init_db
from .routes.abs_proxy import router as abs_proxy_router
from .routes.auth import router as auth_router
from .routes.books import router as books_router
from .routes.downloads import router as downloads_router
from .routes.requests import router as requests_router
from .routes.settings import router as settings_router
from .routes.sync import router as sync_router
from .services.library_sync import sync_library, cache_refresh
from .settings import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Athenaeum")

# Auth router is exempt — no require_auth dependency
app.include_router(auth_router)

# Admin-only routers
app.include_router(settings_router, dependencies=[Depends(require_admin)])
app.include_router(sync_router, dependencies=[Depends(require_admin)])

# User-accessible routers (require auth, role checked per-endpoint where needed)
app.include_router(books_router, dependencies=[Depends(require_auth)])
app.include_router(requests_router, dependencies=[Depends(require_auth)])
app.include_router(downloads_router, dependencies=[Depends(require_auth)])
app.include_router(abs_proxy_router, dependencies=[Depends(require_auth)])
app.mount("/static", StaticFiles(directory="static"), name="static")


async def _wait_until_next(cron_expr: str):
    """Sleep until the next scheduled time for a cron expression."""
    now = datetime.now()
    next_run = croniter(cron_expr, now).get_next(datetime)
    await asyncio.sleep((next_run - now).total_seconds())


async def _task_loop(task_name: str, cron_key: str, task_fn, fallback_interval: int = 0):
    """Supervised loop for a scheduled task.

    fallback_interval: seconds between runs when no cron expression is configured.
    If 0, the loop idles (60s sleep) when unconfigured.
    """
    while True:
        try:
            settings = await get_settings()
            expr = settings.get("schedule", {}).get(cron_key, "")
            if expr:
                await _wait_until_next(expr)
            elif fallback_interval:
                await asyncio.sleep(fallback_interval)
            else:
                await asyncio.sleep(60)
                continue
            await task_fn()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"{task_name} error: {e}", exc_info=True)


async def _cache_refresh_task():
    await cache_refresh()


async def _library_sync_task():
    """Run library sync then kick off HC linking if cache_refresh isn't already running."""
    await sync_library()
    async with get_db() as db:
        row = await (
            await db.execute("SELECT running FROM task_state WHERE task = 'cache_refresh'")
        ).fetchone()
    if not (row and row["running"]):
        asyncio.create_task(_cache_refresh_task())


async def _auto_search_task():
    """Search Prowlarr for all requested items and snatch the first result."""
    from .services.download_clients import prowlarr_search, build_prowlarr_query, QBittorrentClient, SABnzbdClient

    settings = await get_settings()
    prowlarr_settings = settings.get("prowlarr", {})
    if not prowlarr_settings.get("url") or not prowlarr_settings.get("api_key"):
        return

    general = settings.get("general", {})

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT r.id, r.type, r.narrator, b.title,
                          (SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id
                           WHERE ba.book_id = r.book_id ORDER BY ba.author_position LIMIT 1) as author
                   FROM requests r JOIN books b ON b.id = r.book_id
                   WHERE r.status = 'requested'"""
            )
        ).fetchall()

    for row in rows:
        try:
            query = build_prowlarr_query(row["title"], row["author"] or "")
            fmt_key = "allowed_audiobook_formats" if row["type"] == "audiobook" else "allowed_ebook_formats"
            results = await prowlarr_search(
                prowlarr_settings, query,
                book_type=row["type"],
                title=row["title"], author=row["author"] or "",
                allowed_formats=general.get(fmt_key) or [],
            )
            if not results:
                continue

            best = results[0]
            protocol = best.get("protocol")
            download_url = best.get("downloadUrl") or ""
            if not download_url:
                continue

            if protocol == "torrent":
                client_settings = settings.get("qbittorrent", {})
                if not client_settings.get("url"):
                    continue
                client = QBittorrentClient(client_settings)
                client_name = "qbittorrent"
            elif protocol == "usenet":
                client_settings = settings.get("sabnzbd", {})
                if not client_settings.get("url"):
                    continue
                client = SABnzbdClient(client_settings)
                client_name = "sabnzbd"
            else:
                continue

            download_id = await client.add(download_url)
            now = datetime.utcnow().isoformat()
            import uuid as _uuid
            dl_id = str(_uuid.uuid4())
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO downloads
                       (id, request_id, title, indexer, guid, info_url, protocol,
                        size, download_client, download_id, status, grabbed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'snatched', ?)""",
                    (dl_id, row["id"], best.get("title"), best.get("indexer"),
                     best.get("guid"), best.get("infoUrl"), protocol,
                     best.get("size"), client_name, download_id, now),
                )
                await db.execute(
                    "UPDATE requests SET status='snatched', updated_at=? WHERE id=?",
                    (now, row["id"]),
                )
                await db.commit()

        except Exception as e:
            logger.warning("auto_search: failed for request %s: %s", row["id"], e)


async def _download_monitor_tick():
    from .services.download_clients import QBittorrentClient, SABnzbdClient
    from .services.organizer import auto_organize, auto_organize_series_pack, compute_series_pack_mappings

    settings = await get_settings()
    qbit_settings = settings.get("qbittorrent", {})
    sab_settings = settings.get("sabnzbd", {})

    async with get_db() as db:
        rows = await (
            await db.execute(
                """SELECT d.id as dl_id, d.download_id, d.download_client, d.request_id,
                          r.status as req_status
                   FROM downloads d JOIN requests r ON r.id = d.request_id
                   WHERE r.status IN ('snatched', 'downloading')
                   AND d.download_client IS NOT NULL
                   AND d.download_id IS NOT NULL"""
            )
        ).fetchall()

    for row in rows:
        try:
            if row["download_client"] == "qbittorrent":
                if not qbit_settings.get("url"):
                    continue
                client = QBittorrentClient(qbit_settings)
            elif row["download_client"] == "sabnzbd":
                if not sab_settings.get("url"):
                    continue
                client = SABnzbdClient(sab_settings)
            else:
                continue

            info = await client.check(row["download_id"])
            status = info.get("status")
            now = datetime.utcnow().isoformat()

            async with get_db() as db:
                if status == "downloading" and row["req_status"] == "snatched":
                    await db.execute(
                        "UPDATE downloads SET status='downloading' WHERE id=?", (row["dl_id"],)
                    )
                    await db.execute(
                        "UPDATE requests SET status='downloading', updated_at=? WHERE id=?",
                        (now, row["request_id"]),
                    )
                    await db.commit()
                elif status == "completed":
                    path = info.get("path") or ""
                    await db.execute(
                        "UPDATE downloads SET status='completed', download_path=? WHERE id=?",
                        (path, row["dl_id"]),
                    )
                    await db.execute(
                        "UPDATE requests SET status='downloaded', updated_at=? WHERE id=?",
                        (now, row["request_id"]),
                    )
                    await db.commit()
                    asyncio.create_task(auto_organize(row["request_id"]))
                elif status == "failed":
                    await db.execute(
                        "UPDATE downloads SET status='failed' WHERE id=?", (row["dl_id"],)
                    )
                    await db.execute(
                        "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                        (now, row["request_id"]),
                    )
                    await db.commit()

        except Exception as e:
            logger.warning("download_monitor_tick: error for download %s: %s", row["dl_id"], e)

    # Monitor series pack downloads
    async with get_db() as db:
        sd_rows = await (
            await db.execute(
                """SELECT id, download_id, download_client, status
                   FROM series_downloads
                   WHERE status IN ('snatched', 'downloading')
                   AND download_client IS NOT NULL
                   AND download_id IS NOT NULL"""
            )
        ).fetchall()

    for row in sd_rows:
        try:
            if row["download_client"] == "qbittorrent":
                if not qbit_settings.get("url"):
                    continue
                client = QBittorrentClient(qbit_settings)
            elif row["download_client"] == "sabnzbd":
                if not sab_settings.get("url"):
                    continue
                client = SABnzbdClient(sab_settings)
            else:
                continue

            info = await client.check(row["download_id"])
            status = info.get("status")
            now = datetime.utcnow().isoformat()

            async with get_db() as db:
                if status == "downloading" and row["status"] == "snatched":
                    await db.execute(
                        "UPDATE series_downloads SET status='downloading', updated_at=? WHERE id=?",
                        (now, row["id"]),
                    )
                    await db.commit()
                elif status == "completed":
                    path = info.get("path") or ""
                    await db.execute(
                        "UPDATE series_downloads SET status='downloaded', download_path=?, updated_at=? WHERE id=?",
                        (path, now, row["id"]),
                    )
                    await db.commit()
                    asyncio.create_task(compute_series_pack_mappings(row["id"]))
                elif status == "failed":
                    await db.execute(
                        "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                        (now, row["id"]),
                    )
                    await db.commit()

        except Exception as e:
            logger.warning("download_monitor_tick: error for series_download %s: %s", row["id"], e)


async def _download_monitor():
    while True:
        try:
            await _download_monitor_tick()
        except Exception as e:
            logger.error("download_monitor error: %s", e, exc_info=True)
        await asyncio.sleep(15)


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialised")
    async with get_db() as db:
        await db.execute("UPDATE task_state SET running = 0 WHERE running = 1")
        await db.commit()
    logger.info("Cleared stale task running flags")

    # Re-queue any requests that were mid-organize when the container last stopped
    from .services.organizer import auto_organize, auto_organize_series_pack, compute_series_pack_mappings
    async with get_db() as db:
        stale = await (
            await db.execute(
                "SELECT id FROM requests WHERE status IN ('downloaded', 'organizing', 'merging')"
            )
        ).fetchall()
    for row in stale:
        logger.info("Re-queuing stale organize for request %s", row["id"])
        asyncio.create_task(auto_organize(row["id"]))

    # Re-queue stale series pack downloads
    async with get_db() as db:
        stale_packs = await (
            await db.execute(
                "SELECT id, status FROM series_downloads WHERE status IN ('downloaded', 'organizing')"
            )
        ).fetchall()
    for row in stale_packs:
        if row["status"] == "downloaded":
            logger.info("Re-queuing stale series pack mapping compute for %s", row["id"])
            asyncio.create_task(compute_series_pack_mappings(row["id"]))
        else:
            logger.info("Re-queuing stale series pack organize for %s", row["id"])
            asyncio.create_task(auto_organize_series_pack(row["id"]))

    await ensure_session_secret()
    asyncio.create_task(_download_monitor())
    asyncio.create_task(_task_loop("library_sync_task", "library_sync", _library_sync_task, fallback_interval=1800))
    asyncio.create_task(_task_loop("cache_refresh_task", "cache_refresh", _cache_refresh_task))
    asyncio.create_task(_task_loop("auto_search_task", "auto_search", _auto_search_task))


@app.get("/healthz", include_in_schema=False)
async def healthz():
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=503, content={"ok": False, "error": str(e)})


@app.get("/api/status")
async def api_status():
    async with get_db() as db:
        books_row = await (await db.execute("SELECT COUNT(*) FROM books")).fetchone()
        authors_row = await (await db.execute("SELECT COUNT(*) FROM authors")).fetchone()
        series_row = await (await db.execute("SELECT COUNT(*) FROM series")).fetchone()

        unlinked_books_row = await (await db.execute(
            "SELECT COUNT(*) FROM book_links WHERE hardcover_id IS NULL OR hardcover_id = ''"
        )).fetchone()
        unlinked_authors_row = await (await db.execute(
            "SELECT COUNT(*) FROM author_links WHERE hardcover_author_id IS NULL OR hardcover_author_id = ''"
        )).fetchone()
        unlinked_series_row = await (await db.execute(
            "SELECT COUNT(*) FROM series_links WHERE hardcover_series_id IS NULL OR hardcover_series_id = ''"
        )).fetchone()

        audiobooks_row = await (await db.execute(
            "SELECT COUNT(DISTINCT book_id) FROM book_formats WHERE type = 'audiobook'"
        )).fetchone()
        ebooks_row = await (await db.execute(
            "SELECT COUNT(DISTINCT book_id) FROM book_formats WHERE type = 'ebook'"
        )).fetchone()

        statuses = [
            "requested", "snatched", "downloading",
            "downloaded", "merging", "organizing", "completed", "failed",
        ]
        requests = {}
        for status in statuses:
            row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM requests WHERE status = ?", (status,)
                )
            ).fetchone()
            requests[status] = row[0]

    return {
        "books": books_row[0],
        "authors": authors_row[0],
        "series": series_row[0],
        "audiobooks": audiobooks_row[0],
        "ebooks": ebooks_row[0],
        "unlinked_books": unlinked_books_row[0],
        "unlinked_authors": unlinked_authors_row[0],
        "unlinked_series": unlinked_series_row[0],
        "requests": requests,
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})
