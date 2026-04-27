import secrets
from datetime import datetime, timezone, timedelta

from fastapi import Depends, HTTPException, Request, Response
from jose import JWTError, jwt

from .settings import get_settings, save_settings

ALGORITHM = "HS256"


def _auth_active(settings: dict) -> bool:
    auth = settings.get("auth", {})
    return auth.get("form_enabled") or auth.get("oidc_enabled")


def _active_modes(settings: dict) -> list[str]:
    auth = settings.get("auth", {})
    modes = []
    if auth.get("form_enabled"):
        modes.append("form")
    if auth.get("oidc_enabled"):
        modes.append("oidc")
    return modes


async def ensure_session_secret():
    """Auto-generate session_secret if not set. Called on startup."""
    settings = await get_settings()
    if not settings.get("auth", {}).get("session_secret"):
        await save_settings({"auth": {"session_secret": secrets.token_hex(32)}})


def _make_session_token(user_id: str, role: str, secret: str, days: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=int(days))
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, secret, algorithm=ALGORITHM)


def set_session_cookie(response: Response, token: str, request: Request, days: int):
    secure = request.headers.get("x-forwarded-proto", "http") == "https"
    response.set_cookie(
        "session", token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=days * 86400,
        path="/",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie("session", path="/")


async def require_auth(request: Request) -> dict:
    """Returns {user_id, role} or raises 401. Passthrough when auth is disabled."""
    settings = await get_settings()
    if not _auth_active(settings):
        return {"user_id": "anonymous", "role": "admin"}
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, detail={"modes": _active_modes(settings)})
    try:
        secret = settings["auth"]["session_secret"]
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return {"user_id": payload["sub"], "role": payload["role"]}
    except JWTError:
        raise HTTPException(401, detail={"modes": _active_modes(settings)})


async def require_admin(auth: dict = Depends(require_auth)) -> dict:
    if auth["role"] != "admin":
        raise HTTPException(403, "Admin required")
    return auth
