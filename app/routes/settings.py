import os
from datetime import datetime

import httpx
from croniter import croniter
from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..services.audiobookshelf import AudiobookshelfService
from ..settings import get_settings, save_settings

router = APIRouter(prefix="/api")

KNOWN_SECTIONS = frozenset([
    "prowlarr", "qbittorrent", "sabnzbd", "audiobookshelf",
    "hardcover", "pushover", "general", "schedule", "auth",
])

SENSITIVE_KEYS = frozenset([
    "api_key", "password", "app_token", "user_key",
    "oidc_client_secret", "password_hash", "session_secret",
])

PATH_KEYS = frozenset(["output_dir", "download_dir"])


def _mask_sensitive(settings: dict) -> dict:
    result = {}
    for section, values in settings.items():
        if isinstance(values, dict):
            masked = {}
            for k, v in values.items():
                masked[k] = "********" if (k in SENSITIVE_KEYS and v) else v
            result[section] = masked
        else:
            result[section] = values
    return result


def _strip_sentinels(partial: dict) -> dict:
    result = {}
    for section, values in partial.items():
        if isinstance(values, dict):
            result[section] = {k: v for k, v in values.items() if v != "********"}
        else:
            result[section] = values
    return result


@router.get("/settings")
async def get_settings_route():
    settings = await get_settings()
    return _mask_sensitive(settings)


@router.put("/settings")
async def put_settings_route(body: dict):
    unknown = set(body.keys()) - KNOWN_SECTIONS
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown settings sections: {sorted(unknown)}",
        )

    for section, values in body.items():
        if isinstance(values, dict):
            for k, v in values.items():
                if k in PATH_KEYS and v and not os.path.exists(v):
                    raise HTTPException(status_code=400, detail=f"Path does not exist: {v}")

    if "schedule" in body and isinstance(body["schedule"], dict):
        for field, expr in body["schedule"].items():
            if expr:
                try:
                    croniter(expr, datetime.now())
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid cron expression: {field}",
                    )

    await save_settings(_strip_sentinels(body))
    return {"ok": True}


def _merge_with_saved(saved: dict, body: dict) -> dict:
    """Overlay form values onto saved config, ignoring sentinel placeholders."""
    return {**saved, **{k: v for k, v in body.items() if v != "********"}}


@router.post("/settings/test/abs")
async def test_abs(body: dict = None):
    settings = await get_settings()
    cfg = _merge_with_saved(settings.get("audiobookshelf", {}), body or {})
    svc = AudiobookshelfService(cfg)
    if not svc.base_url:
        raise HTTPException(status_code=400, detail="AudiobookShelf URL not configured")
    try:
        return await svc.test_connection()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/settings/test/prowlarr")
async def test_prowlarr(body: dict = None):
    settings = await get_settings()
    cfg = _merge_with_saved(settings.get("prowlarr", {}), body or {})
    url = cfg.get("url", "").rstrip("/")
    api_key = cfg.get("api_key", "")
    if not url:
        raise HTTPException(status_code=400, detail="Prowlarr URL not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{url}/api/v1/system/status",
                headers={"X-Api-Key": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"version": data.get("version", ""), "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/settings/test/qbittorrent")
async def test_qbittorrent(body: dict = None):
    settings = await get_settings()
    cfg = _merge_with_saved(settings.get("qbittorrent", {}), body or {})
    url = cfg.get("url", "").rstrip("/")
    username = cfg.get("username", "")
    password = cfg.get("password", "")
    if not url:
        raise HTTPException(status_code=400, detail="qBittorrent URL not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            login_resp = await client.post(
                f"{url}/api/v2/auth/login",
                data={"username": username, "password": password},
            )
            if login_resp.text.strip().lower() != "ok.":
                raise Exception("Login failed — check username and password")
            version_resp = await client.get(f"{url}/api/v2/app/version")
            version_resp.raise_for_status()
            return {"version": version_resp.text.strip(), "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/settings/test/hardcover")
async def test_hardcover(body: dict = None):
    settings = await get_settings()
    cfg = _merge_with_saved(settings.get("hardcover", {}), body or {})
    api_key = cfg.get("api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Hardcover API key not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": "{ me { id username } }"},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            me_raw = data.get("data", {}).get("me") or {}
            me = me_raw[0] if isinstance(me_raw, list) else me_raw
            if not me:
                raise Exception("Authentication failed — check your API key")
            return {"username": me.get("username", ""), "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/settings/test/sabnzbd")
async def test_sabnzbd(body: dict = None):
    settings = await get_settings()
    cfg = _merge_with_saved(settings.get("sabnzbd", {}), body or {})
    url = cfg.get("url", "").rstrip("/")
    api_key = cfg.get("api_key", "")
    if not url:
        raise HTTPException(status_code=400, detail="SABnzbd URL not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{url}/api",
                params={"mode": "version", "output": "json", "apikey": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"version": data.get("version", ""), "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/schedule/next-run")
async def get_next_run(expr: str):
    try:
        nxt = croniter(expr, datetime.now()).get_next(datetime)
        return {"next_run": nxt.isoformat()}
    except Exception:
        return {"next_run": None}


TASK_NAMES = ["library_sync", "cache_refresh", "auto_search"]


@router.get("/sync/status")
async def get_sync_status():
    settings = await get_settings()
    schedule = settings.get("schedule", {})
    now = datetime.now()

    next_runs = {}
    for task in TASK_NAMES:
        expr = schedule.get(task, "")
        if expr:
            try:
                next_runs[task] = croniter(expr, now).get_next(datetime).isoformat()
            except Exception:
                next_runs[task] = None
        else:
            next_runs[task] = None

    async with get_db() as db:
        rows = await (
            await db.execute(
                "SELECT task, running, last_run, last_result FROM task_state WHERE task IN (?, ?, ?)",
                TASK_NAMES,
            )
        ).fetchall()

    state = {task: {"running": False, "last_run": None, "last_result": None} for task in TASK_NAMES}
    for row in rows:
        state[row[0]] = {
            "running": bool(row[1]),
            "last_run": row[2],
            "last_result": row[3],
        }

    return {
        task: {**state[task], "next_run": next_runs[task]}
        for task in TASK_NAMES
    }
