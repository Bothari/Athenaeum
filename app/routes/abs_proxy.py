from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

from ..settings import get_settings

router = APIRouter(prefix="/api/abs")


@router.get("/library-settings")
async def get_library_settings():
    """Return ABS library-level settings relevant to display (coverAspectRatio: 1=square, 0=tall)."""
    settings = await get_settings()
    abs_cfg = settings.get("audiobookshelf", {})
    base_url = (abs_cfg.get("url") or "").rstrip("/")
    api_key = abs_cfg.get("api_key") or ""
    library_ids = abs_cfg.get("library_id") or []
    if isinstance(library_ids, str):
        library_ids = [library_ids] if library_ids else []

    if not base_url or not library_ids:
        return {"cover_aspect_ratio": 1}

    lib_id = library_ids[0]
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/libraries/{lib_id}", headers=headers)
            resp.raise_for_status()
            lib_settings = resp.json().get("settings", {})
            return {"cover_aspect_ratio": lib_settings.get("coverAspectRatio", 1)}
    except Exception:
        return {"cover_aspect_ratio": 1}


@router.get("/cover/{abs_id}")
async def proxy_abs_cover(abs_id: str):
    settings = await get_settings()
    abs_cfg = settings.get("audiobookshelf", {})
    base_url = (abs_cfg.get("url") or "").rstrip("/")
    api_key = abs_cfg.get("api_key") or ""
    if not base_url:
        raise HTTPException(status_code=503, detail="ABS not configured")

    url = f"{base_url}/api/items/{abs_id}/cover"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Cover not found")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
