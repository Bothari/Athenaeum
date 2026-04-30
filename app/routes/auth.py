import asyncio
import base64
import hashlib
import json
import logging
import secrets
import time
import uuid
from urllib.parse import urlencode
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext
from pydantic import BaseModel

from ..auth import (
    _active_modes, _auth_active, _make_session_token,
    clear_session_cookie, require_admin, require_auth, set_session_cookie,
)
from ..database import get_db
from ..settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory OIDC discovery cache: {provider_url: (expires_ts, config_dict)}
_oidc_discovery_cache: dict = {}
_oidc_discovery_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── OIDC discovery ─────────────────────────────────────────────────────────────

async def _get_oidc_config(provider_url: str) -> dict:
    async with _oidc_discovery_lock:
        cached = _oidc_discovery_cache.get(provider_url)
        if cached and cached[0] > time.time():
            return cached[1]

    url = provider_url.rstrip("/") + "/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        config = resp.json()

    async with _oidc_discovery_lock:
        _oidc_discovery_cache[provider_url] = (time.time() + 3600, config)

    return config


async def _get_jwks(jwks_uri: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()
        return resp.json()


# ── Auth routes ────────────────────────────────────────────────────────────────

class VerifyOidcBody(BaseModel):
    provider_url: str


@router.post("/auth/oidc/verify")
async def verify_oidc_provider(body: VerifyOidcBody, auth: dict = Depends(require_admin)):
    """Fetch OIDC discovery document and return key endpoints for UI confirmation."""
    try:
        config = await _get_oidc_config(body.provider_url)
    except Exception as e:
        raise HTTPException(400, f"Could not reach provider: {e}")
    return {
        "ok": True,
        "issuer": config.get("issuer", ""),
        "authorization_endpoint": config.get("authorization_endpoint", ""),
        "token_endpoint": config.get("token_endpoint", ""),
        "userinfo_endpoint": config.get("userinfo_endpoint", ""),
    }


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(body: LoginBody, request: Request, response: Response):
    settings = await get_settings()
    if not settings.get("auth", {}).get("form_enabled"):
        raise HTTPException(400, "Form login is not enabled")

    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT id, username, password_hash, role, force_password_change FROM users WHERE username = ?",
                (body.username,),
            )
        ).fetchone()

    if not row or not row["password_hash"] or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    secret = settings["auth"]["session_secret"]
    days = int(settings["auth"].get("session_days", 30))
    token = _make_session_token(row["id"], row["role"], secret, days)
    set_session_cookie(response, token, request, days)
    return {
        "ok": True,
        "username": row["username"],
        "role": row["role"],
        "force_password_change": bool(row["force_password_change"]),
    }


@router.post("/auth/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/auth/me")
async def me(request: Request):
    settings = await get_settings()
    if not _auth_active(settings):
        return {"user_id": "anonymous", "role": "admin", "username": "anonymous", "force_password_change": False}

    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, detail={"modes": _active_modes(settings)})

    from jose import JWTError, jwt as jose_jwt
    try:
        secret = settings["auth"]["session_secret"]
        payload = jose_jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(401, detail={"modes": _active_modes(settings)})

    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT username, email, role, force_password_change FROM users WHERE id = ?",
                (user_id,),
            )
        ).fetchone()

    if not row:
        raise HTTPException(401, detail={"modes": _active_modes(settings)})

    return {
        "user_id": user_id,
        "username": row["username"],
        "email": row["email"] or "",
        "role": row["role"],
        "force_password_change": bool(row["force_password_change"]),
    }


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordBody, auth: dict = Depends(require_auth)):
    if auth["user_id"] == "anonymous":
        raise HTTPException(400, "Auth not enabled")
    async with get_db() as db:
        row = await (
            await db.execute(
                "SELECT password_hash FROM users WHERE id = ?", (auth["user_id"],)
            )
        ).fetchone()
        if not row or not verify_password(body.current_password, row["password_hash"]):
            raise HTTPException(401, "Current password incorrect")
        await db.execute(
            "UPDATE users SET password_hash=?, force_password_change=0, updated_at=? WHERE id=?",
            (hash_password(body.new_password), _now(), auth["user_id"]),
        )
        await db.commit()
    return {"ok": True}


# ── OIDC ───────────────────────────────────────────────────────────────────────

@router.get("/auth/oidc/start")
async def oidc_start(request: Request, response: Response):
    settings = await get_settings()
    auth_cfg = settings.get("auth", {})
    if not auth_cfg.get("oidc_enabled"):
        raise HTTPException(400, "OIDC not enabled")

    provider_url = auth_cfg.get("oidc_provider_url", "")
    client_id = auth_cfg.get("oidc_client_id", "")
    scopes = auth_cfg.get("oidc_scopes", "openid email profile")

    config = await _get_oidc_config(provider_url)
    auth_endpoint = config["authorization_endpoint"]

    state = secrets.token_hex(16)
    nonce = secrets.token_hex(16)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    oidc_state_payload = json.dumps({"state": state, "nonce": nonce, "cv": code_verifier})

    secure = request.headers.get("x-forwarded-proto", "http") == "https"

    public_url = settings.get("general", {}).get("public_url", "").rstrip("/")
    redirect_uri = f"{public_url}/api/auth/oidc/callback"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    redirect = RedirectResponse(f"{auth_endpoint}?{urlencode(params)}", status_code=302)
    redirect.set_cookie(
        "oidc_state", oidc_state_payload,
        httponly=True, samesite="lax", secure=secure,
        max_age=600, path="/",
    )
    return redirect


@router.get("/auth/oidc/callback")
async def oidc_callback(request: Request, response: Response, code: str = "", state: str = ""):
    settings = await get_settings()
    auth_cfg = settings.get("auth", {})

    oidc_state_raw = request.cookies.get("oidc_state")
    if not oidc_state_raw:
        raise HTTPException(400, "Missing OIDC state cookie")
    try:
        oidc_state = json.loads(oidc_state_raw)
    except Exception:
        raise HTTPException(400, "Invalid OIDC state cookie")

    if oidc_state.get("state") != state:
        raise HTTPException(400, "State mismatch")

    provider_url = auth_cfg.get("oidc_provider_url", "")
    client_id = auth_cfg.get("oidc_client_id", "")
    client_secret = auth_cfg.get("oidc_client_secret", "")
    public_url = settings.get("general", {}).get("public_url", "").rstrip("/")
    redirect_uri = f"{public_url}/api/auth/oidc/callback"

    config = await _get_oidc_config(provider_url)
    token_endpoint = config["token_endpoint"]
    jwks_uri = config["jwks_uri"]

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(token_endpoint, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": oidc_state["cv"],
        })
        if not token_resp.is_success:
            logger.error("OIDC token exchange failed %s: %s", token_resp.status_code, token_resp.text)
            raise HTTPException(400, f"OIDC token exchange failed: {token_resp.text}")
        token_data = token_resp.json()

    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(400, "No id_token in OIDC response")

    jwks = await _get_jwks(jwks_uri)
    from jose import jwt as jose_jwt, JWTError
    try:
        claims = jose_jwt.decode(
            id_token, jwks,
            algorithms=["RS256", "HS256"],
            audience=client_id,
        )
    except JWTError as e:
        raise HTTPException(400, f"ID token verification failed: {e}")

    if claims.get("nonce") != oidc_state.get("nonce"):
        raise HTTPException(400, "Nonce mismatch")

    oidc_sub = claims["sub"]
    email = claims.get("email", "")

    async with get_db() as db:
        # Look up by oidc_sub first
        row = await (
            await db.execute("SELECT id, role FROM users WHERE oidc_sub = ?", (oidc_sub,))
        ).fetchone()

        if not row and email:
            row = await (
                await db.execute("SELECT id, role FROM users WHERE email = ?", (email,))
            ).fetchone()
            if row:
                await db.execute(
                    "UPDATE users SET oidc_sub=?, updated_at=? WHERE id=?",
                    (oidc_sub, _now(), row["id"]),
                )
                await db.commit()

        if not row:
            oidc_username = claims.get("preferred_username", "")
            if oidc_username:
                row = await (
                    await db.execute("SELECT id, role FROM users WHERE username = ?", (oidc_username,))
                ).fetchone()
                if row:
                    await db.execute(
                        "UPDATE users SET oidc_sub=?, updated_at=? WHERE id=?",
                        (oidc_sub, _now(), row["id"]),
                    )
                    await db.commit()

        if not row:
            # Auto-provision new user
            new_id = str(uuid.uuid4())
            username = email.split("@")[0] if email else oidc_sub[:20]
            now = _now()
            await db.execute(
                """INSERT INTO users (id, username, email, role, oidc_sub, created_at, updated_at)
                   VALUES (?, ?, ?, 'user', ?, ?, ?)""",
                (new_id, username, email, oidc_sub, now, now),
            )
            await db.commit()
            user_id = new_id
            role = "user"
        else:
            user_id = row["id"]
            role = row["role"]

    secret = settings["auth"]["session_secret"]
    days = int(auth_cfg.get("session_days", 30))
    token = _make_session_token(user_id, role, secret, days)
    # Return a 200 HTML page that redirects client-side. Cookies set on a 200
    # response are reliably persisted by browsers; cookies on a 302 in a
    # cross-site redirect chain (Authentik → Athenaeum → /) can be dropped.
    html = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/'></head><body></body></html>"
    resp = HTMLResponse(html)
    resp.delete_cookie("oidc_state", path="/")
    set_session_cookie(resp, token, request, days)
    return resp


# ── User management (admin only) ───────────────────────────────────────────────

class CreateUserBody(BaseModel):
    username: str
    password: str
    role: str = "user"
    email: str | None = None


class PatchUserBody(BaseModel):
    role: str | None = None
    email: str | None = None


class ResetPasswordBody(BaseModel):
    new_password: str


@router.get("/users")
async def list_users(auth: dict = Depends(require_admin)):
    async with get_db() as db:
        rows = await (
            await db.execute(
                "SELECT id, username, email, role, force_password_change, created_at, (oidc_sub IS NOT NULL AND oidc_sub != '') AS oidc_linked FROM users ORDER BY created_at"
            )
        ).fetchall()
    return {"users": [dict(r) for r in rows]}


@router.post("/users")
async def create_user(body: CreateUserBody, auth: dict = Depends(require_admin)):
    if body.role not in ("admin", "user"):
        raise HTTPException(400, "role must be admin or user")
    new_id = str(uuid.uuid4())
    now = _now()
    async with get_db() as db:
        try:
            await db.execute(
                """INSERT INTO users (id, username, email, role, password_hash, force_password_change, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (new_id, body.username, body.email or "", body.role, hash_password(body.password), now, now),
            )
            await db.commit()
        except Exception:
            raise HTTPException(409, "Username already exists")
    return {"id": new_id, "username": body.username, "role": body.role, "force_password_change": True}


@router.patch("/users/{user_id}")
async def patch_user(user_id: str, body: PatchUserBody, auth: dict = Depends(require_admin)):
    if body.role is not None and body.role not in ("admin", "user"):
        raise HTTPException(400, "role must be admin or user")
    async with get_db() as db:
        row = await (await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if body.role is not None:
            await db.execute(
                "UPDATE users SET role=?, updated_at=? WHERE id=?",
                (body.role, _now(), user_id),
            )
        if body.email is not None:
            await db.execute(
                "UPDATE users SET email=?, updated_at=? WHERE id=?",
                (body.email, _now(), user_id),
            )
        await db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, auth: dict = Depends(require_admin)):
    if user_id == auth["user_id"]:
        raise HTTPException(400, "Cannot delete yourself")
    async with get_db() as db:
        row = await (await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
async def reset_password(user_id: str, body: ResetPasswordBody, auth: dict = Depends(require_admin)):
    async with get_db() as db:
        row = await (await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        await db.execute(
            "UPDATE users SET password_hash=?, force_password_change=1, updated_at=? WHERE id=?",
            (hash_password(body.new_password), _now(), user_id),
        )
        await db.commit()
    return {"ok": True}
