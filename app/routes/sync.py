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


@router.post("/sync/auto-search")
async def trigger_auto_search():
    asyncio.create_task(_run_auto_search())
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


async def _run_auto_search():
    from ..services.auto_search import run_auto_search_all
    try:
        await run_auto_search_all()
    except Exception as e:
        logger.error(f"Manual auto-search failed: {e}", exc_info=True)


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
    hardcover_slug: str = ""


@router.put("/sync/link/book/{book_id}")
async def set_book_link(book_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    hc_slug = body.hardcover_slug.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE book_links SET hardcover_id = ?, hardcover_slug = ? WHERE book_id = ?",
            (hc_id, hc_slug, book_id),
        )
        await db.commit()

    # Fetch and store release_date from HC when a link is set
    if hc_id:
        try:
            settings = await get_settings()
            api_key = settings.get("hardcover", {}).get("api_key") or ""
            if api_key:
                from ..services.library_sync import _fetch_hc_release_date
                release_date = await _fetch_hc_release_date(int(hc_id), api_key)
                if release_date:
                    async with get_db() as db:
                        await db.execute(
                            "UPDATE books SET release_date = ? WHERE id = ?",
                            (release_date, book_id),
                        )
                        await db.commit()
        except Exception as e:
            logger.warning("Failed to fetch release_date for book %s: %s", book_id, e)

    return {"ok": True, "hardcover_id": hc_id, "hardcover_slug": hc_slug}


@router.put("/sync/link/author/{author_id}")
async def set_author_link(author_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    hc_slug = body.hardcover_slug.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE author_links SET hardcover_author_id = ?, hardcover_author_slug = ? WHERE author_id = ?",
            (hc_id, hc_slug, author_id),
        )
        await db.commit()
    return {"ok": True, "hardcover_id": hc_id, "hardcover_slug": hc_slug}


@router.put("/sync/link/series/{series_id}")
async def set_series_link(series_id: str, body: SetLinkBody):
    hc_id = body.hardcover_id.strip() or None
    hc_slug = body.hardcover_slug.strip() or None
    async with get_db() as db:
        await db.execute(
            "UPDATE series_links SET hardcover_series_id = ?, hardcover_series_slug = ? WHERE series_id = ?",
            (hc_id, hc_slug, series_id),
        )
        await db.commit()
    return {"ok": True, "hardcover_id": hc_id, "hardcover_slug": hc_slug}


class ResolveUrlBody(BaseModel):
    url: str
    type: str


@router.post("/sync/resolve-hc-url")
async def resolve_hc_url(body: ResolveUrlBody):
    """Resolve a Hardcover URL to a numeric ID + slug by searching for the slug."""
    from urllib.parse import urlparse
    import httpx

    slug = urlparse(body.url).path.strip("/").split("/")[-1]
    if not slug:
        return {"error": "Could not extract slug from URL"}

    query_type_map = {"book": "Book", "author": "author", "series": "series"}
    query_type = query_type_map.get(body.type, "Book")
    query = slug.replace("-", " ")

    settings = await get_settings()
    api_key = settings.get("hardcover", {}).get("api_key", "")
    if not api_key:
        return {"error": "No Hardcover API key configured"}

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={
                    "query": 'query Search($q: String!) { search(query: $q, query_type: $qt, per_page: 10) { results } }'.replace("$qt", f'"{query_type}"'),
                    "variables": {"q": query},
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            hits = resp.json()["data"]["search"]["results"].get("hits", [])
    except Exception as e:
        return {"error": str(e)}

    for hit in hits:
        doc = hit.get("document", {})
        if doc.get("slug") == slug:
            return {"hardcover_id": str(doc["id"]), "hardcover_slug": slug}

    return {"error": f"No HC item found with slug '{slug}'"}
