import asyncio
import base64
import hashlib
import logging
import re
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

# __Host- prefixed so the browser enforces Secure + Path=/ + no Domain on it.
_OIDC_STATE_COOKIE = "__Host-oidc_state"


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

    base = provider_url.rstrip("/")
    url = base + "/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        config = resp.json()

    # Pin the discovery issuer to the configured provider_url. The ID-token issuer
    # check trusts config["issuer"]; if we accepted whatever the discovery document
    # declared as its own issuer, a spoofed/hijacked discovery endpoint could claim
    # an arbitrary issuer and we would "verify" tokens against that same value —
    # a circular trust with no anchor. The admin-configured provider_url IS the
    # anchor, so the discovery doc's issuer must match it exactly.
    doc_issuer = str(config.get("issuer", "")).rstrip("/")
    if doc_issuer != base:
        raise HTTPException(
            400, f"OIDC discovery issuer mismatch: {config.get('issuer')!r} != {provider_url!r}"
        )

    async with _oidc_discovery_lock:
        _oidc_discovery_cache[provider_url] = (time.time() + 3600, config)

    return config


async def _get_jwks(jwks_uri: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()
        return resp.json()


# A host authority is host[:port]. Allow DNS/host chars + optional port only. Any
# comma (list), whitespace, or "@" (userinfo -> the real host is AFTER the @, so
# `trusted@attacker` would resolve to attacker) makes it untrusted.
_VALID_HOST_RE = re.compile(r"^[A-Za-z0-9.\-]+(:[0-9]+)?$")


def _clean_host(value: str | None) -> str:
    """Return `value` only if it is a single, well-formed host authority; otherwise
    "". Applied to BOTH X-Forwarded-Host and the fallback Host header — an
    unsanitized fallback is just as poisonable (`Host: good, attacker` or
    `trusted@attacker`) and would corrupt the redirect_uri (open-redirect /
    token-exfil)."""
    if value is None:
        return ""
    value = value.strip()
    if not value or not _VALID_HOST_RE.match(value):
        return ""
    return value


def _redirect_uri(request: Request, settings: dict) -> str:
    """Absolute OIDC callback URL. Prefer the configured public_url; otherwise
    infer it from the reverse proxy's forwarded headers (Traefik/Nginx set these).
    A relative redirect_uri is rejected by every OIDC provider, so this must always
    return an absolute URL."""
    public_url = settings.get("general", {}).get("public_url", "").rstrip("/")
    if public_url:
        return f"{public_url}/api/auth/oidc/callback"

    # OIDC callbacks are https-only; an inferred http base is never valid, so we
    # never trust an http x-forwarded-proto for inference — https is the only
    # acceptable inferred scheme.
    proto = "https"

    # Every candidate host is sanitized identically — never trust a fallback more
    # than the forwarded header.
    host = (
        _clean_host(request.headers.get("x-forwarded-host"))
        or _clean_host(request.headers.get("host"))
        or _clean_host(request.url.netloc)
    )
    if not host:
        raise HTTPException(400, "Cannot determine a valid OIDC redirect_uri host")
    return f"{proto}://{host}/api/auth/oidc/callback"


def _encode_oidc_state(payload: dict, secret: str) -> str:
    """Sign the OIDC state (state/nonce/PKCE verifier/redirect_uri) so the client
    cannot tamper with it. Stored in a cookie between /start and /callback; an
    unsigned cookie would let a client forge the redirect_uri or PKCE verifier."""
    from jose import jwt as jose_jwt
    return jose_jwt.encode(
        {**payload, "exp": int(time.time()) + 600}, secret, algorithm="HS256"
    )


def _decode_oidc_state(raw: str, secret: str) -> dict:
    from jose import jwt as jose_jwt
    return jose_jwt.decode(raw, secret, algorithms=["HS256"])


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

    # Compute the redirect_uri ONCE here and carry it (signed) to the callback, so
    # the token-exchange redirect_uri is byte-identical to this authorize request's
    # even if the callback arrives with different Host/X-Forwarded-* headers.
    redirect_uri = _redirect_uri(request, settings)
    oidc_state_payload = _encode_oidc_state(
        {"state": state, "nonce": nonce, "cv": code_verifier, "redirect_uri": redirect_uri},
        auth_cfg["session_secret"],
    )

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
    # __Host- prefix hardens the state cookie: the browser rejects it unless it is
    # Secure, Path=/, and carries no Domain — closing subdomain/insecure cookie
    # injection. OIDC is https-only, so secure=True is unconditional.
    redirect.set_cookie(
        _OIDC_STATE_COOKIE, oidc_state_payload,
        httponly=True, samesite="lax", secure=True,
        max_age=600, path="/",
    )
    return redirect


class _OidcError(Exception):
    """Internal: an expected OIDC callback failure. status is the HTTP status to
    return to the browser; detail is logged server-side only and NEVER reflected to
    the client (avoids leaking provider text / MIME-sniff vectors)."""
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


async def _provision_oidc_user(db, *, oidc_iss: str, oidc_sub: str,
                               base_username: str, stored_email: str) -> str:
    """Insert a new OIDC-provisioned 'user' account, tolerating a concurrent
    UNIQUE(username) collision. A check-then-INSERT races under concurrency and
    500s on the constraint; instead we attempt the INSERT and, on IntegrityError,
    retry with the next username suffix in a bounded loop. Returns the new user id."""
    import sqlite3
    base = (base_username or "user")[:32] or "user"
    for n in range(1, 51):
        candidate = base if n == 1 else f"{base[:24]}-{n}"
        new_id = str(uuid.uuid4())
        now = _now()
        try:
            await db.execute(
                """INSERT INTO users (id, username, email, role, oidc_sub, oidc_iss, created_at, updated_at)
                   VALUES (?, ?, ?, 'user', ?, ?, ?, ?)""",
                (new_id, candidate, stored_email, oidc_sub, oidc_iss, now, now),
            )
            await db.commit()
            return new_id
        except sqlite3.IntegrityError:
            # Roll back the failed INSERT and try the next suffix. A (oidc_iss,
            # oidc_sub) collision here means a concurrent request already provisioned
            # this identity — fall through and let the caller re-select it.
            await db.rollback()
            existing = await (
                await db.execute(
                    "SELECT id FROM users WHERE oidc_iss = ? AND oidc_sub = ?",
                    (oidc_iss, oidc_sub),
                )
            ).fetchone()
            if existing:
                return existing["id"]
            continue
    raise _OidcError(500, "Could not allocate a unique username for OIDC user")


@router.get("/auth/oidc/callback")
async def oidc_callback(request: Request, response: Response, code: str = "", state: str = ""):
    settings = await get_settings()
    auth_cfg = settings.get("auth", {})

    oidc_state_raw = request.cookies.get(_OIDC_STATE_COOKIE)
    if not oidc_state_raw:
        # No cookie to clear; a plain 400 is correct here.
        return _oidc_error_response(400)

    # ALL processing runs inside this try so that EVERY exit — expected rejection,
    # discovery/network/JWKS/DB error, or malformed token JSON — returns a response
    # that clears the one-time __Host- state cookie (fail-closed) with no reflected
    # provider text.
    try:
        return await _oidc_callback_inner(request, settings, auth_cfg,
                                          oidc_state_raw, code, state)
    except _OidcError as e:
        logger.warning("OIDC callback rejected (%s): %s", e.status, e.detail)
        return _oidc_error_response(e.status)
    except Exception:
        logger.exception("OIDC callback failed unexpectedly")
        return _oidc_error_response(500)


def _oidc_error_response(status: int) -> Response:
    """Generic error response for the OIDC callback: fixed text/plain body (no
    provider text), Cache-Control: no-store, and a fail-closed deletion of the
    __Host- state cookie. The delete_cookie MUST carry secure=True + path=/ or the
    browser rejects the deletion of a __Host- cookie and it survives."""
    resp = Response(status_code=status, content="OIDC login failed",
                    media_type="text/plain", headers={"Cache-Control": "no-store"})
    resp.delete_cookie(_OIDC_STATE_COOKIE, path="/", secure=True, samesite="lax", httponly=True)
    return resp


async def _oidc_callback_inner(request: Request, settings: dict, auth_cfg: dict,
                               oidc_state_raw: str, code: str, state: str) -> Response:
    from jose import JWTError
    try:
        # Verify the signature — a tampered state cookie (forged redirect_uri,
        # PKCE verifier, or nonce) is rejected here.
        oidc_state = _decode_oidc_state(oidc_state_raw, auth_cfg["session_secret"])
    except JWTError:
        raise _OidcError(400, "Invalid OIDC state cookie")

    if oidc_state.get("state") != state:
        raise _OidcError(400, "State mismatch")

    provider_url = auth_cfg.get("oidc_provider_url", "")
    client_id = auth_cfg.get("oidc_client_id", "")
    client_secret = auth_cfg.get("oidc_client_secret", "")
    # Use the redirect_uri computed at /start (signed into the state cookie), NOT a
    # value recomputed from this request — the token exchange requires it to match
    # the authorize request's redirect_uri exactly.
    redirect_uri = oidc_state["redirect_uri"]

    try:
        config = await _get_oidc_config(provider_url)
    except HTTPException as e:
        raise _OidcError(e.status_code, str(e.detail))
    token_endpoint = config["token_endpoint"]
    jwks_uri = config["jwks_uri"]

    # Token-endpoint client authentication method (OIDC Core §9). This is a property
    # of THIS CLIENT'S registration at the provider, NOT of the provider's global
    # capabilities — so it must NOT be inferred from token_endpoint_auth_methods_supported
    # (that advertises every method the SERVER offers; a client registered for
    # client_secret_post gets `invalid_client` if we pick basic just because the
    # server also supports basic). Default to client_secret_post — the method this
    # app has always used and the one existing deployments are registered for — and
    # honour an explicit override. Validate the provider actually supports the chosen
    # method when it advertises the list.
    method = auth_cfg.get("oidc_token_endpoint_auth_method") or "client_secret_post"
    if method not in ("client_secret_post", "client_secret_basic"):
        raise _OidcError(400, f"Unsupported oidc_token_endpoint_auth_method: {method!r}")
    supported = config.get("token_endpoint_auth_methods_supported")
    if supported is not None and method not in supported:
        raise _OidcError(400, f"Provider does not support {method!r}: {supported}")
    use_basic = (method == "client_secret_basic")

    token_body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        # PKCE verifier always travels in the body regardless of client-auth method.
        "code_verifier": oidc_state["cv"],
    }
    basic_auth = None
    if use_basic:
        basic_auth = httpx.BasicAuth(client_id, client_secret)
    else:
        token_body["client_secret"] = client_secret

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(token_endpoint, data=token_body, auth=basic_auth)
        if not token_resp.is_success:
            # Log the provider's text server-side; never reflect it to the client.
            logger.error("OIDC token exchange failed %s: %s", token_resp.status_code, token_resp.text)
            raise _OidcError(400, "OIDC token exchange failed")
        token_data = token_resp.json()

    id_token = token_data.get("id_token")
    access_token = token_data.get("access_token")
    # Both must be present and string-valued — a non-string (or absent) value would
    # otherwise surface as a 500/KeyError deep in decode() instead of a clean 400.
    if not isinstance(id_token, str) or not id_token:
        raise _OidcError(400, "No valid id_token in OIDC response")
    if not isinstance(access_token, str) or not access_token:
        raise _OidcError(400, "No valid access_token in OIDC response")

    jwks = await _get_jwks(jwks_uri)
    from jose import jwt as jose_jwt
    try:
        claims = jose_jwt.decode(
            id_token, jwks,
            # Only asymmetric algorithms — the key material here is the provider's
            # JWKS. HS256 must not be allowed alongside a JWKS: it is both dead
            # (an HMAC alg cannot verify against a public JWK) and an algorithm-
            # confusion vector (an attacker could sign a token with the public key
            # treated as an HMAC secret).
            algorithms=["RS256", "ES256"],
            audience=client_id,
            # Verify the issuer so a token minted by a different (valid-signature)
            # issuer cannot be accepted.
            issuer=config["issuer"],
            # Pass the access_token so python-jose can verify the at_hash claim when
            # present. Providers such as Authelia include at_hash in authorization-
            # code ID tokens; without the access_token, decode() would raise on it.
            access_token=access_token,
            # python-jose defaults every require_* to False, so aud/exp/iat/iss/sub
            # are only checked WHEN PRESENT. Force them to be present — an ID token
            # missing exp/aud/iss/sub is not a valid OIDC ID token and must be
            # rejected, not silently accepted. at_hash stays optional (verified only
            # when present) since not every provider emits it.
            options={
                "require_aud": True,
                "require_exp": True,
                "require_iat": True,
                "require_iss": True,
                "require_sub": True,
                "require_nonce": False,
            },
        )
    except JWTError as e:
        raise _OidcError(400, f"ID token verification failed: {e}")

    # azp (authorized party): when present it MUST equal our client_id. This catches
    # a token that was issued to a different client but happens to include us in aud.
    azp = claims.get("azp")
    if azp is not None and azp != client_id:
        raise _OidcError(400, "Token azp does not match client_id")

    # audience: python-jose accepts a token whose aud array merely CONTAINS our
    # client_id. Tighten it — reject any extra (untrusted) audience so a token
    # shared with another RP cannot be replayed here.
    aud = claims.get("aud")
    if isinstance(aud, (list, tuple)):
        if set(aud) - {client_id}:
            raise _OidcError(400, "Token audience contains untrusted entries")
    elif aud != client_id:
        raise _OidcError(400, "Token audience mismatch")

    # Nonce binds the token to THIS login attempt. Use .get on both sides so a
    # missing/non-string nonce is a clean 400, never a 500.
    if claims.get("nonce") != oidc_state.get("nonce"):
        raise _OidcError(400, "Nonce mismatch")

    oidc_sub = claims.get("sub")
    if not isinstance(oidc_sub, str) or not oidc_sub:
        raise _OidcError(400, "Missing sub claim")
    # Identity is the (issuer, subject) pair. Pin the issuer to the verified token
    # iss (already == config["issuer"], which is itself pinned to provider_url).
    oidc_iss = claims.get("iss")
    if not isinstance(oidc_iss, str) or not oidc_iss:
        raise _OidcError(400, "Missing iss claim")
    email = claims.get("email", "") or ""
    if not isinstance(email, str):
        email = ""
    # A verified email is ONLY the boolean True. Many IdPs send the STRING "false";
    # bool("false") is True, so a truthiness test would wrongly treat it as verified.
    email_verified = claims.get("email_verified") is True

    async with get_db() as db:
        # Link an existing local account ONLY by the stable (oidc_iss, oidc_sub)
        # identity. Email/username linking is deliberately absent: email can be
        # unverified, reassigned, or collide across issuers, and username is
        # attacker-selectable — either would let a federated user bind onto and
        # inherit the role of an existing local account (account takeover). Unknown
        # identities are auto-provisioned as a brand-new 'user'; we NEVER merge onto
        # an existing account.
        row = await (
            await db.execute(
                "SELECT id, role FROM users WHERE oidc_iss = ? AND oidc_sub = ?",
                (oidc_iss, oidc_sub),
            )
        ).fetchone()

        if not row:
            # Store the email only when verified; otherwise keep it empty so an
            # unverified (attacker-chosen) address never lands in the account.
            stored_email = email if email_verified else ""
            base_username = (
                email.split("@")[0] if (email_verified and email) else oidc_sub[:20]
            )
            user_id = await _provision_oidc_user(
                db, oidc_iss=oidc_iss, oidc_sub=oidc_sub,
                base_username=base_username, stored_email=stored_email,
            )
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
    # no-store so the browser/proxy never caches a page whose request carried the
    # auth code and whose response sets the session cookie.
    html = "<!DOCTYPE html><html><head><meta http-equiv='refresh' content='0;url=/'></head><body></body></html>"
    resp = HTMLResponse(html, headers={"Cache-Control": "no-store"})
    # __Host- deletion MUST carry secure=True + path=/ or the browser rejects it.
    resp.delete_cookie(_OIDC_STATE_COOKIE, path="/", secure=True, samesite="lax", httponly=True)
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
