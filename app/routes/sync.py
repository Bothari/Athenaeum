import asyncio
import logging

from fastapi import APIRouter

from ..services.library_sync import sync_library

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.post("/sync/library")
async def trigger_library_sync():
    asyncio.create_task(_run_sync())
    return {"ok": True}


@router.post("/sync/cache-refresh")
async def trigger_cache_refresh():
    # Placeholder — implemented in Phase 4
    return {"ok": True}


async def _run_sync():
    try:
        result = await sync_library()
        logger.info(f"Manual library sync complete: {result}")
    except Exception as e:
        logger.error(f"Manual library sync failed: {e}", exc_info=True)
