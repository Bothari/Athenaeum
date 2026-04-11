import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from ..database import get_db
from ..services.library_sync import sync_library, cache_refresh, try_link_book, try_link_author, try_link_series
from ..settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.post("/sync/library")
async def trigger_library_sync():
    asyncio.create_task(_run_sync())
    return {"ok": True}


@router.post("/sync/cache-refresh")
async def trigger_cache_refresh():
    asyncio.create_task(_run_cache_refresh())
    return {"ok": True}


async def _run_sync():
    try:
        result = await sync_library()
        logger.info(f"Manual library sync complete: {result}")
    except Exception as e:
        logger.error(f"Manual library sync failed: {e}", exc_info=True)
        return
    # Kick off HC linking for newly synced books if not already running
    async with get_db() as db:
        row = await (
            await db.execute("SELECT running FROM task_state WHERE task = 'cache_refresh'")
        ).fetchone()
    if not (row and row["running"]):
        asyncio.create_task(_run_cache_refresh())


async def _run_cache_refresh():
    try:
        await cache_refresh()
    except Exception as e:
        logger.error(f"Manual cache refresh failed: {e}", exc_info=True)


@router.post("/sync/try-link/book/{book_id}")
async def try_link_book_endpoint(book_id: str):
    settings = await get_settings()
    return await try_link_book(book_id, settings)


@router.post("/sync/try-link/author/{author_id}")
async def try_link_author_endpoint(author_id: str):
    settings = await get_settings()
    return await try_link_author(author_id, settings)


@router.post("/sync/try-link/series/{series_id}")
async def try_link_series_endpoint(series_id: str):
    settings = await get_settings()
    return await try_link_series(series_id, settings)


class SetLinkBody(BaseModel):
    hardcover_id: str


@router.put("/sync/link/book/{book_id}")
async def set_book_link(book_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE book_links SET hardcover_id = ? WHERE book_id = ?",
            (hc_id, book_id),
        )
        await db.commit()
    return {"ok": True, "hardcover_id": hc_id}


@router.put("/sync/link/author/{author_id}")
async def set_author_link(author_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE author_links SET hardcover_author_id = ? WHERE author_id = ?",
            (hc_id, author_id),
        )
        await db.commit()
    return {"ok": True, "hardcover_id": hc_id}


@router.put("/sync/link/series/{series_id}")
async def set_series_link(series_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE series_links SET hardcover_series_id = ? WHERE series_id = ?",
            (hc_id, series_id),
        )
        await db.commit()
    return {"ok": True, "hardcover_id": hc_id}
