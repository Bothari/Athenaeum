import asyncio
import logging

from fastapi import APIRouter

from ..database import get_db
from ..services.library_sync import sync_library, cache_refresh

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
