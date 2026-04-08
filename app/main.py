import asyncio
import logging
from datetime import datetime

from croniter import croniter
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db, init_db
from .routes.abs_proxy import router as abs_proxy_router
from .routes.books import router as books_router
from .routes.settings import router as settings_router
from .routes.sync import router as sync_router
from .services.library_sync import sync_library, cache_refresh
from .settings import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Athenaeum")

app.include_router(settings_router)
app.include_router(books_router)
app.include_router(sync_router)
app.include_router(abs_proxy_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


async def _wait_until_next(cron_expr: str):
    """Sleep until the next scheduled time for a cron expression."""
    now = datetime.now()
    next_run = croniter(cron_expr, now).get_next(datetime)
    await asyncio.sleep((next_run - now).total_seconds())


async def _task_loop(task_name: str, cron_key: str, task_fn):
    """Supervised loop for a scheduled task."""
    while True:
        try:
            settings = await get_settings()
            expr = settings.get("schedule", {}).get(cron_key, "")
            if not expr:
                await asyncio.sleep(60)
                continue
            await _wait_until_next(expr)
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
    """Placeholder — implemented in Phase 5."""
    pass


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialised")
    async with get_db() as db:
        await db.execute("UPDATE task_state SET running = 0 WHERE running = 1")
        await db.commit()
    logger.info("Cleared stale task running flags")
    asyncio.create_task(_task_loop("library_sync_task", "library_sync", _library_sync_task))
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

        statuses = [
            "requested", "snatched", "downloading",
            "downloaded", "merging", "organizing", "in_library", "failed",
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
        "unlinked_books": unlinked_books_row[0],
        "unlinked_authors": unlinked_authors_row[0],
        "unlinked_series": unlinked_series_row[0],
        "requests": requests,
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})
