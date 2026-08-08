"""OIDC login flow regression tests.

Covers two fixed bugs and their security hardening:
  - ID-token validation in oidc_callback (at_hash + issuer + asymmetric-only algs).
  - Absolute redirect_uri (inferred when public_url is unset), computed once at
    /start and carried, signed, to the callback.

The tests drive the real /start -> /callback flow so they are agnostic to the
state-cookie's internal format (it is a signed JWT).
"""
import base64
import hashlib
import time
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from app.main import app
from app import settings as settings_module
from app.routes import auth as auth_routes

ISSUER = "https://idp.example.com"
CLIENT_ID = "athenaeum"
SESSION_SECRET = "test-session-secret"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"
TOKEN_URL = f"{ISSUER}/token"
JWKS_URL = f"{ISSUER}/jwks"
AUTH_URL = f"{ISSUER}/authorize"

DISCOVERY_DOC = {
    "issuer": ISSUER,
    "authorization_endpoint": AUTH_URL,
    "token_endpoint": TOKEN_URL,
    "jwks_uri": JWKS_URL,
}


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def rsa_key_and_jwks():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    nums = key.public_key().public_numbers()

    def uint(n: int) -> str:
        return _b64u(n.to_bytes((n.bit_length() + 7) // 8, "big"))

    jwks = {"keys": [{"kty": "RSA", "kid": "test", "use": "sig", "alg": "RS256",
                      "n": uint(nums.n), "e": uint(nums.e)}]}
    return priv_pem, jwks


def _at_hash(access_token: str) -> str:
    # OIDC: base64url(left-most half of SHA-256(access_token)) for RS256/ES256.
    return _b64u(hashlib.sha256(access_token.encode()).digest()[:16])


_OMIT = object()


def _make_id_token(priv_pem, *, access_token, nonce, iss=ISSUER, aud=CLIENT_ID,
                   at_hash=_OMIT, sub="user-sub-1", email="reader@example.com",
                   email_verified=None, preferred_username=None, alg="RS256", key=None,
                   azp=None, exp=_OMIT, drop_aud=False, drop_iat=False,
                   drop_nonce=False):
    now = int(time.time())
    claims = {"iss": iss, "sub": sub, "aud": aud, "email": email, "nonce": nonce,
              "iat": now}
    # at_hash: _OMIT -> compute a matching one; None -> leave the claim out entirely
    # (optional claim); any explicit value -> use it verbatim (mismatch tests).
    if at_hash is _OMIT:
        claims["at_hash"] = _at_hash(access_token)
    elif at_hash is not None:
        claims["at_hash"] = at_hash
    if exp is _OMIT:
        claims["exp"] = now + 300
    elif exp is not None:
        claims["exp"] = exp
    if drop_aud:
        claims.pop("aud", None)
    if drop_iat:
        claims.pop("iat", None)
    if drop_nonce:
        claims.pop("nonce", None)
    if email_verified is not None:
        claims["email_verified"] = email_verified
    if preferred_username is not None:
        claims["preferred_username"] = preferred_username
    if azp is not None:
        claims["azp"] = azp
    return jose_jwt.encode(claims, key or priv_pem, algorithm=alg,
                           headers={"kid": "test"})


_OIDC_AUTH = {
    "oidc_enabled": True,
    "oidc_provider_url": ISSUER,
    "oidc_client_id": CLIENT_ID,
    "oidc_client_secret": "client-secret",
    "oidc_scopes": "openid email profile",
    "session_secret": SESSION_SECRET,
    "session_days": 30,
}


async def _setup(tmp_path, monkeypatch, c, general=None):
    """One passthrough settings PUT (auth still disabled at that instant), so both
    auth and general land before OIDC gates future writes."""
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    auth_routes._oidc_discovery_cache.clear()  # cross-test isolation
    body = {"auth": dict(_OIDC_AUTH)}
    if general is not None:
        body["general"] = general
    await c.put("/api/settings", json=body)


@pytest_asyncio.fixture
async def oidc_client(db_path, tmp_path, monkeypatch):
    """OIDC enabled; public_url unset (exercises inference)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as c:
        await _setup(tmp_path, monkeypatch, c)
        yield c


@pytest_asyncio.fixture
async def oidc_client_pub(db_path, tmp_path, monkeypatch):
    """OIDC enabled with an explicit public_url set from the start."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as c:
        await _setup(tmp_path, monkeypatch, c, general={"public_url": "https://canonical.example.com"})
        yield c


async def _start(client, httpx_mock, headers=None):
    """Drive /start; return (state, nonce, redirect_uri) from the signed cookie."""
    httpx_mock.add_response(url=DISCOVERY_URL, json=DISCOVERY_DOC)
    resp = await client.get("/api/auth/oidc/start", headers=headers or {},
                            follow_redirects=False)
    assert resp.status_code == 302
    cookie = client.cookies.get("__Host-oidc_state")
    payload = jose_jwt.decode(cookie, SESSION_SECRET, algorithms=["HS256"])
    loc = parse_qs(urlparse(resp.headers["location"]).query)
    return payload["state"], payload["nonce"], payload["redirect_uri"], loc


# ── ID-token validation (bug #1 + hardening) ────────────────────────────────────

@pytest.mark.asyncio
async def test_login_succeeds_with_at_hash_and_issuer(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _redirect, _loc = await _start(oidc_client, httpx_mock)
    access_token = "an-access-token"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 200, resp.text
    assert oidc_client.cookies.get("session")  # session issued


@pytest.mark.asyncio
async def test_rejects_mismatched_at_hash(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    access_token = "real-access-token"
    bad = _at_hash("a-different-token")  # at_hash does NOT match access_token
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce, at_hash=bad)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_wrong_issuer(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce,
                              iss="https://evil.example.com")  # wrong iss
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400


# ── redirect_uri (bug #2) ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_infers_absolute_redirect_uri_when_public_url_unset(oidc_client, httpx_mock):
    _s, _n, redirect_uri, loc = await _start(
        oidc_client, httpx_mock,
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "books.example.com"},
    )
    assert redirect_uri == "https://books.example.com/api/auth/oidc/callback"
    # and it's carried into the authorize request (absolute, not relative)
    assert loc["redirect_uri"] == ["https://books.example.com/api/auth/oidc/callback"]


@pytest.mark.asyncio
async def test_start_prefers_explicit_public_url(oidc_client_pub, httpx_mock):
    # public_url set; inference must NOT be used even with a misleading forwarded host
    _s, _n, redirect_uri, _l = await _start(
        oidc_client_pub, httpx_mock, headers={"X-Forwarded-Host": "attacker.example.com"})
    assert redirect_uri == "https://canonical.example.com/api/auth/oidc/callback"


@pytest.mark.asyncio
async def test_callback_uses_stored_redirect_uri_not_recomputed(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, redirect_uri, _l = await _start(
        oidc_client, httpx_mock,
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "books.example.com"})
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    # callback arrives with a DIFFERENT host — the stored redirect_uri must still be sent
    await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                          headers={"X-Forwarded-Host": "evil.example.com"},
                          follow_redirects=False)
    token_req = next(r for r in httpx_mock.get_requests() if r.url == TOKEN_URL and r.method == "POST")
    sent = parse_qs(token_req.content.decode())
    assert sent["redirect_uri"] == ["https://books.example.com/api/auth/oidc/callback"]


@pytest.mark.asyncio
async def test_rejects_wrong_secret_state_cookie(oidc_client):
    # A STRUCTURALLY VALID state JWT signed with the WRONG secret must be rejected —
    # this pins that the signature is actually verified (a malformed string would be
    # rejected even without signature checking, so it would not pin the fix).
    forged = jose_jwt.encode(
        {"state": "s", "nonce": "n", "cv": "v",
         "redirect_uri": "https://evil.example.com/api/auth/oidc/callback",
         "exp": int(time.time()) + 600},
        "the-WRONG-secret", algorithm="HS256")
    resp = await oidc_client.get(
        "/api/auth/oidc/callback?code=abc&state=s",
        headers={"Cookie": f"__Host-oidc_state={forged}"}, follow_redirects=False)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_rejects_expired_state_cookie(oidc_client):
    expired = jose_jwt.encode(
        {"state": "s", "nonce": "n", "cv": "v",
         "redirect_uri": "https://test/api/auth/oidc/callback",
         "exp": int(time.time()) - 10},  # already expired
        SESSION_SECRET, algorithm="HS256")
    resp = await oidc_client.get(
        "/api/auth/oidc/callback?code=abc&state=s",
        headers={"Cookie": f"__Host-oidc_state={expired}"}, follow_redirects=False)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_rejects_hs256_id_token(oidc_client, rsa_key_and_jwks, httpx_mock):
    # An HS256-signed ID token must be rejected because only RS256/ES256 are
    # accepted. To TRULY pin algorithms=["RS256","ES256"] (and not merely trip a
    # "wrong key type" error), the mocked JWKS carries a matching `oct` key whose
    # `k` is the attacker's HMAC secret. So if HS256 were in the allowed list this
    # token WOULD validate and the test would fail — which is exactly the confusion
    # vector we are closing.
    priv_pem, jwks = rsa_key_and_jwks
    hmac_secret = "attacker-secret"
    oct_jwk = {"kty": "oct", "kid": "test", "use": "sig", "alg": "HS256",
               "k": _b64u(hmac_secret.encode())}
    poisoned_jwks = {"keys": list(jwks["keys"]) + [oct_jwk]}
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    access_token = "tok"
    hs_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce,
                              alg="HS256", key=hmac_secret)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": hs_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=poisoned_jwks)
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


async def _insert_user(username, email, role="admin"):
    from app.database import get_db
    import uuid as _uuid
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, username, email, role, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(_uuid.uuid4()), username, email, role, "2026-01-01", "2026-01-01"))
        await db.commit()


async def _complete_login(client, httpx_mock, priv_pem, jwks, **id_token_kwargs):
    state, nonce, _r, _l = await _start(client, httpx_mock)
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce, **id_token_kwargs)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    return await client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                            follow_redirects=False)


@pytest.mark.asyncio
async def test_does_not_link_existing_account_by_username(oidc_client, rsa_key_and_jwks, httpx_mock):
    # An attacker whose IdP lets them set preferred_username="admin" must NOT be
    # linked to the local admin account (account takeover / privilege escalation).
    priv_pem, jwks = rsa_key_and_jwks
    await _insert_user("admin", "realadmin@example.com", role="admin")
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="attacker-sub", email="attacker@evil.example",
                                 email_verified=True, preferred_username="admin")
    assert resp.status_code == 200  # login succeeds, but as a NEW non-admin user
    from app.database import get_db
    async with get_db() as db:
        # the local admin's oidc_sub must NOT have been bound to the attacker
        row = await (await db.execute(
            "SELECT oidc_sub, role FROM users WHERE username = 'admin'")).fetchone()
        assert row["oidc_sub"] in (None, "")  # admin NOT hijacked
        attacker = await (await db.execute(
            "SELECT role FROM users WHERE oidc_sub = 'attacker-sub'")).fetchone()
        assert attacker["role"] == "user"  # provisioned as plain user, not admin


@pytest.mark.asyncio
async def test_does_not_link_by_unverified_email(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    await _insert_user("boss", "boss@example.com", role="admin")
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="attacker2", email="boss@example.com",
                                 email_verified=False)  # unverified — must NOT link
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT oidc_sub FROM users WHERE username = 'boss'")).fetchone()
        assert row["oidc_sub"] in (None, "")


@pytest.mark.asyncio
async def test_does_not_link_by_verified_email(oidc_client, rsa_key_and_jwks, httpx_mock):
    # Safe (iss,sub) model: even a VERIFIED email matching a local account must NOT
    # link — email can be reassigned/collide across issuers. The OIDC user is
    # provisioned as a brand-new account; the local one is untouched.
    priv_pem, jwks = rsa_key_and_jwks
    await _insert_user("member", "member@example.com", role="user")
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="member-sub", email="member@example.com",
                                 email_verified=True)
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT oidc_sub FROM users WHERE username = 'member'")).fetchone()
        assert row["oidc_sub"] in (None, "")  # local account NOT linked
        provisioned = await (await db.execute(
            "SELECT role, oidc_sub FROM users WHERE oidc_sub = 'member-sub'")).fetchone()
        assert provisioned["role"] == "user"  # a fresh account was created


# ── Legacy adoption (rows linked before migration 15) ───────────────────────────

ISSUER2 = "https://idp2.example.com"


async def _insert_legacy_oidc_user(username, sub, role="admin"):
    """A pre-migration-15 row: linked by oidc_sub alone, oidc_iss left NULL by the
    migration backfill."""
    from app.database import get_db
    import uuid as _uuid
    uid = str(_uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, username, email, role, oidc_sub, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, username, "", role, sub, "2026-01-01", "2026-01-01"))
        await db.commit()
    return uid


@pytest.mark.asyncio
async def test_legacy_account_adopted_on_first_login(oidc_client, rsa_key_and_jwks, httpx_mock):
    # Migration 15 backfills oidc_iss as NULL, which the (iss, sub) lookup can never
    # match — the first post-migration login must ADOPT the legacy row (stamp the
    # verified issuer, keep id and role), not provision a duplicate 'user' account.
    priv_pem, jwks = rsa_key_and_jwks
    uid = await _insert_legacy_oidc_user("boss", "legacy-sub", role="admin")
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="legacy-sub")
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        n = (await (await db.execute("SELECT COUNT(*) AS n FROM users")).fetchone())["n"]
        assert n == 1  # adopted, not duplicated
        row = await (await db.execute(
            "SELECT id, role, oidc_iss FROM users WHERE oidc_sub = 'legacy-sub'")).fetchone()
        assert row["id"] == uid
        assert row["role"] == "admin"
        assert row["oidc_iss"] == ISSUER
    me = await oidc_client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "boss"
    assert me.json()["role"] == "admin"  # session carries the preserved role


@pytest.mark.asyncio
async def test_adoption_claims_only_matching_sub(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    await _insert_legacy_oidc_user("alice", "legacy-a", role="user")
    await _insert_legacy_oidc_user("bob", "legacy-b", role="user")
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="legacy-a")
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        a = await (await db.execute(
            "SELECT oidc_iss FROM users WHERE oidc_sub = 'legacy-a'")).fetchone()
        b = await (await db.execute(
            "SELECT oidc_iss FROM users WHERE oidc_sub = 'legacy-b'")).fetchone()
        assert a["oidc_iss"] == ISSUER
        assert b["oidc_iss"] is None  # other legacy rows untouched


@pytest.mark.asyncio
async def test_adopted_account_second_login_stable(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    uid = await _insert_legacy_oidc_user("carol", "legacy-c", role="admin")
    r1 = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="legacy-c")
    assert r1.status_code == 200
    oidc_client.cookies.clear()
    auth_routes._oidc_discovery_cache.clear()  # force the 2nd /start to re-fetch discovery
    r2 = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="legacy-c")
    assert r2.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        rows = await (await db.execute("SELECT id, role FROM users")).fetchall()
        assert len(rows) == 1
        assert rows[0]["id"] == uid
        assert rows[0]["role"] == "admin"


@pytest.mark.asyncio
async def test_adopted_row_not_reclaimable_by_other_issuer(
        oidc_client, rsa_key_and_jwks, httpx_mock, tmp_path, monkeypatch):
    # Adoption is one-time: once stamped with issuer A, a login from issuer B
    # presenting the SAME sub must not re-claim the row — B gets a fresh account.
    priv_pem, jwks = rsa_key_and_jwks
    uid = await _insert_legacy_oidc_user("dave", "legacy-d", role="admin")
    r1 = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="legacy-d")
    assert r1.status_code == 200

    # Repoint the app at a second provider. A fresh settings file starts with auth
    # disabled, so the passthrough PUT works exactly as in _setup.
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(tmp_path / "settings2.yaml"))
    auth_routes._oidc_discovery_cache.clear()
    await oidc_client.put("/api/settings", json={
        "auth": {**_OIDC_AUTH, "oidc_provider_url": ISSUER2}})

    httpx_mock.add_response(
        url=f"{ISSUER2}/.well-known/openid-configuration",
        json={"issuer": ISSUER2, "authorization_endpoint": f"{ISSUER2}/authorize",
              "token_endpoint": f"{ISSUER2}/token", "jwks_uri": f"{ISSUER2}/jwks"})
    resp = await oidc_client.get("/api/auth/oidc/start", follow_redirects=False)
    assert resp.status_code == 302
    payload = jose_jwt.decode(oidc_client.cookies.get("__Host-oidc_state"),
                              SESSION_SECRET, algorithms=["HS256"])
    access_token = "tok2"
    id_token = _make_id_token(priv_pem, access_token=access_token,
                              nonce=payload["nonce"], iss=ISSUER2, sub="legacy-d")
    httpx_mock.add_response(url=f"{ISSUER2}/token",
                            json={"access_token": access_token, "id_token": id_token,
                                  "token_type": "bearer"})
    httpx_mock.add_response(url=f"{ISSUER2}/jwks", json=jwks)
    r2 = await oidc_client.get(
        f"/api/auth/oidc/callback?code=abc&state={payload['state']}",
        follow_redirects=False)
    assert r2.status_code == 200

    from app.database import get_db
    async with get_db() as db:
        orig = await (await db.execute(
            "SELECT role, oidc_iss FROM users WHERE id = ?", (uid,))).fetchone()
        assert orig["oidc_iss"] == ISSUER  # still owned by the first issuer
        assert orig["role"] == "admin"
        newrow = await (await db.execute(
            "SELECT id, role FROM users WHERE oidc_iss = ? AND oidc_sub = 'legacy-d'",
            (ISSUER2,))).fetchone()
        assert newrow is not None
        assert newrow["id"] != uid
        assert newrow["role"] == "user"


# ── Required-claim enforcement (item 1) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejects_id_token_missing_exp(oidc_client, rsa_key_and_jwks, httpx_mock):
    # Same issuer/signature but no exp — python-jose only checks exp when present,
    # so require_exp must force rejection of an unbounded-lifetime token.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, exp=None)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_id_token_missing_aud(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, drop_aud=True)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


# ── azp / audience (item 2) ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejects_wrong_azp(oidc_client, rsa_key_and_jwks, httpx_mock):
    # azp present but not our client_id: token was authorized for another party.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 azp="some-other-client")
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_aud_array_with_untrusted_extra(oidc_client, rsa_key_and_jwks, httpx_mock):
    # aud contains our client_id AND an extra untrusted audience — reject.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 aud=[CLIENT_ID, "other-rp"], azp=CLIENT_ID)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_accepts_aud_array_with_only_client_id(oidc_client, rsa_key_and_jwks, httpx_mock):
    # aud as a single-element array containing ONLY our client_id is valid.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 aud=[CLIENT_ID], azp=CLIENT_ID)
    assert resp.status_code == 200
    assert oidc_client.cookies.get("session")


# ── Discovery issuer pinning (item 3) ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejects_discovery_issuer_mismatch(oidc_client, httpx_mock):
    # Discovery doc whose own "issuer" differs from the configured provider_url must
    # be rejected — closes the circular "trust the doc's own issuer" problem.
    bad_doc = dict(DISCOVERY_DOC, issuer="https://attacker.example.com")
    httpx_mock.add_response(url=DISCOVERY_URL, json=bad_doc)
    resp = await oidc_client.get("/api/auth/oidc/start", follow_redirects=False)
    assert resp.status_code == 400


# ── Cookie hardening (item 5) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_state_cookie_is_host_prefixed_and_secure(oidc_client, httpx_mock):
    httpx_mock.add_response(url=DISCOVERY_URL, json=DISCOVERY_DOC)
    resp = await oidc_client.get("/api/auth/oidc/start", follow_redirects=False)
    assert resp.status_code == 302
    set_cookie = resp.headers["set-cookie"]
    assert set_cookie.startswith("__Host-oidc_state=")
    assert "Secure" in set_cookie
    assert "Path=/" in set_cookie
    assert "Domain" not in set_cookie  # __Host- forbids Domain


# ── Forwarded-header sanitization (item 7) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_start_rejects_comma_list_forwarded_host(oidc_client, httpx_mock):
    # A spoofed comma-list forwarded host must not poison the redirect_uri — the
    # malformed token is ignored and we fall back to the (clean) Host header.
    _s, _n, redirect_uri, _l = await _start(
        oidc_client, httpx_mock,
        headers={"X-Forwarded-Proto": "https",
                 "X-Forwarded-Host": "books.example.com, attacker.example.com"})
    assert "attacker.example.com" not in redirect_uri
    assert redirect_uri == "https://test/api/auth/oidc/callback"


# ── Username-collision-safe provisioning (item 9) ────────────────────────────────

@pytest.mark.asyncio
async def test_colliding_derived_usernames_get_distinct_accounts(oidc_client, rsa_key_and_jwks, httpx_mock):
    # A local 'admin' exists. Two OIDC users whose derived username base is also
    # 'admin' must both provision with DISTINCT usernames, and never hijack the
    # existing local admin.
    priv_pem, jwks = rsa_key_and_jwks
    await _insert_user("admin", "admin@local", role="admin")
    r1 = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                               sub="oidc-1", email="admin@a.example",
                               email_verified=True)
    assert r1.status_code == 200
    oidc_client.cookies.clear()
    auth_routes._oidc_discovery_cache.clear()  # force the 2nd /start to re-fetch discovery
    r2 = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                               sub="oidc-2", email="admin@b.example",
                               email_verified=True)
    assert r2.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        u1 = await (await db.execute(
            "SELECT username, role FROM users WHERE oidc_sub='oidc-1'")).fetchone()
        u2 = await (await db.execute(
            "SELECT username, role FROM users WHERE oidc_sub='oidc-2'")).fetchone()
        local = await (await db.execute(
            "SELECT oidc_sub, role FROM users WHERE username='admin'")).fetchone()
    assert u1["username"] != u2["username"]        # distinct
    assert "admin" not in (u1["username"], u2["username"])  # local 'admin' not reused
    assert u1["role"] == "user" and u2["role"] == "user"
    assert local["oidc_sub"] in (None, "")         # local admin untouched
    assert local["role"] == "admin"


# ── Token-endpoint client auth: client_secret_basic (item 10) ────────────────────

@pytest.mark.asyncio
async def test_uses_client_secret_basic_when_configured(db_path, tmp_path, monkeypatch,
                                                        rsa_key_and_jwks, httpx_mock):
    # The auth method follows the CLIENT's configured registration, not the server's
    # advertised capabilities: configure client_secret_basic -> secret in the header.
    priv_pem, jwks = rsa_key_and_jwks
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as c:
        monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(tmp_path / "settings.yaml"))
        auth_routes._oidc_discovery_cache.clear()
        auth = dict(_OIDC_AUTH, oidc_token_endpoint_auth_method="client_secret_basic")
        await c.put("/api/settings", json={"auth": auth})
        httpx_mock.add_response(url=DISCOVERY_URL, json=dict(
            DISCOVERY_DOC, token_endpoint_auth_methods_supported=["client_secret_basic", "client_secret_post"]))
        await c.get("/api/auth/oidc/start", follow_redirects=False)
        payload = jose_jwt.decode(c.cookies.get("__Host-oidc_state"), SESSION_SECRET, algorithms=["HS256"])
        state, nonce = payload["state"], payload["nonce"]
        access_token = "tok"
        id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
        httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                     "id_token": id_token, "token_type": "bearer"})
        httpx_mock.add_response(url=JWKS_URL, json=jwks)
        await c.get(f"/api/auth/oidc/callback?code=abc&state={state}", follow_redirects=False)
        token_req = next(r for r in httpx_mock.get_requests()
                         if r.url == TOKEN_URL and r.method == "POST")
        assert token_req.headers.get("authorization", "").startswith("Basic ")
        sent = parse_qs(token_req.content.decode())
        assert "client_secret" not in sent  # secret in the header, not the body
        assert sent["code_verifier"]        # PKCE verifier still in the body


# ── Token response typing + Cache-Control (item 11) ──────────────────────────────

@pytest.mark.asyncio
async def test_rejects_non_string_id_token(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": "tok",
                                                 "id_token": {"not": "a string"},
                                                 "token_type": "bearer"})
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400  # clean 400, not a 500/KeyError
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_callback_sets_cache_control_no_store(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks)
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"


# ── Fail-closed state-cookie clearing (BLOCKING 1) ───────────────────────────────

def _deletes_state_cookie(resp) -> bool:
    """True iff the response deletes the __Host- state cookie with Secure set — a
    __Host- deletion WITHOUT Secure is rejected by the browser, so the cookie would
    otherwise survive."""
    for _k, v in resp.headers.multi_items():
        if _k.lower() == "set-cookie" and v.startswith("__Host-oidc_state="):
            # A deletion sets an empty value + Max-Age=0/expiry in the past.
            if ("Max-Age=0" in v or "expires=" in v.lower()) and "Secure" in v:
                return True
    return False


@pytest.mark.asyncio
async def test_success_clears_state_cookie_with_secure(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks)
    assert resp.status_code == 200
    assert _deletes_state_cookie(resp)  # __Host- deletion carries Secure


@pytest.mark.asyncio
async def test_exceptional_path_clears_state_cookie(oidc_client, rsa_key_and_jwks, httpx_mock):
    # Token endpoint returns 500 — an EXCEPTIONAL/error path. It must still clear the
    # one-time state cookie (with Secure) and set Cache-Control: no-store, and must
    # NOT reflect the provider's error text.
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    httpx_mock.add_response(url=TOKEN_URL, status_code=500,
                            text="PROVIDER-SECRET-LEAK-token-error")
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    assert _deletes_state_cookie(resp)
    assert resp.headers.get("cache-control") == "no-store"
    assert "PROVIDER-SECRET-LEAK" not in resp.text  # no reflected provider text
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_jwks_fetch_error_clears_state_cookie(oidc_client, rsa_key_and_jwks, httpx_mock):
    # An unexpected exception (JWKS endpoint 500 -> raise_for_status) must still
    # fail closed: state cookie cleared, no 500-with-stacktrace leak.
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, status_code=500, text="jwks boom")
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code in (400, 500)
    assert _deletes_state_cookie(resp)
    assert "jwks boom" not in resp.text


# ── Redirect-host fallback sanitization (BLOCKING 2) ─────────────────────────────

@pytest.mark.asyncio
async def test_start_rejects_dirty_host_header(oidc_client, httpx_mock):
    # No X-Forwarded-Host; a comma-list in the Host header must NOT be trusted as a
    # fallback. base_url gives Host: test, so we override it with a dirty value.
    httpx_mock.add_response(url=DISCOVERY_URL, json=DISCOVERY_DOC)
    resp = await oidc_client.get(
        "/api/auth/oidc/start",
        headers={"Host": "good.example, attacker.example"}, follow_redirects=False)
    # Every host candidate is dirty -> no valid host -> 400 (not a poisoned redirect).
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_start_rejects_userinfo_forwarded_host(oidc_client, httpx_mock):
    # X-Forwarded-Host: trusted@attacker — the real host is AFTER the @, so this must
    # be rejected, not parsed as "trusted". (_start registers the discovery mock.)
    _s, _n, redirect_uri, _l = await _start(
        oidc_client, httpx_mock,
        headers={"X-Forwarded-Host": "trusted@attacker.example"})
    assert "attacker.example" not in redirect_uri
    assert "trusted@" not in redirect_uri
    # Falls back to the clean Host header (test).
    assert redirect_uri == "https://test/api/auth/oidc/callback"


# ── Token-endpoint client auth method selection (BLOCKING 3) ─────────────────────

async def _start_with_discovery(client, httpx_mock, discovery):
    httpx_mock.add_response(url=DISCOVERY_URL, json=discovery)
    resp = await client.get("/api/auth/oidc/start", follow_redirects=False)
    assert resp.status_code == 302
    cookie = client.cookies.get("__Host-oidc_state")
    payload = jose_jwt.decode(cookie, SESSION_SECRET, algorithms=["HS256"])
    return payload["state"], payload["nonce"]


@pytest.mark.asyncio
async def test_client_secret_post_when_only_post_advertised(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    doc = dict(DISCOVERY_DOC, token_endpoint_auth_methods_supported=["client_secret_post"])
    state, nonce = await _start_with_discovery(oidc_client, httpx_mock, doc)
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                          follow_redirects=False)
    token_req = next(r for r in httpx_mock.get_requests()
                     if r.url == TOKEN_URL and r.method == "POST")
    assert "authorization" not in {k.lower() for k in token_req.headers}  # no Basic
    sent = parse_qs(token_req.content.decode())
    assert sent["client_secret"] == ["client-secret"]  # secret in the body


@pytest.mark.asyncio
async def test_client_secret_post_is_default(oidc_client, rsa_key_and_jwks, httpx_mock):
    # No oidc_token_endpoint_auth_method configured -> default client_secret_post
    # (the method existing deployments are registered for): secret in the body, no
    # Basic header. (DISCOVERY_DOC omits token_endpoint_auth_methods_supported.)
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce = await _start_with_discovery(oidc_client, httpx_mock, dict(DISCOVERY_DOC))
    access_token = "tok"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": access_token,
                                                 "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)
    await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                          follow_redirects=False)
    token_req = next(r for r in httpx_mock.get_requests()
                     if r.url == TOKEN_URL and r.method == "POST")
    assert not token_req.headers.get("authorization")  # no Basic header
    assert parse_qs(token_req.content.decode())["client_secret"] == ["client-secret"]


@pytest.mark.asyncio
async def test_rejects_unsupported_client_auth_methods(oidc_client, rsa_key_and_jwks, httpx_mock):
    # token_endpoint_auth_methods_supported advertises NEITHER basic NOR post -> must
    # reject and NEVER send the secret anywhere.
    priv_pem, jwks = rsa_key_and_jwks
    doc = dict(DISCOVERY_DOC, token_endpoint_auth_methods_supported=["private_key_jwt"])
    state, nonce = await _start_with_discovery(oidc_client, httpx_mock, doc)
    # No token/JWKS responses are registered because no exchange should occur.
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    # No POST to the token endpoint happened -> the secret was never sent.
    assert not any(r.url == TOKEN_URL and r.method == "POST"
                   for r in httpx_mock.get_requests())


# ── (iss,sub) identity + email_verified bug (BLOCKING 4) ─────────────────────────

@pytest.mark.asyncio
async def test_same_sub_different_issuer_does_not_inherit(oidc_client, rsa_key_and_jwks, httpx_mock):
    # Seed an admin account bound to a DIFFERENT issuer but the SAME sub value the
    # incoming token will carry. Because identity is (iss, sub) — not sub alone — the
    # login must NOT match/inherit that admin: it provisions a fresh 'user' scoped to
    # OUR issuer. (Revert to sub-only lookup and this account gets hijacked -> fail.)
    priv_pem, jwks = rsa_key_and_jwks
    from app.database import get_db
    import uuid as _uuid
    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, username, email, role, oidc_sub, oidc_iss, created_at, updated_at) "
            "VALUES (?, 'legit-admin', '', 'admin', 'shared-sub', ?, '2026-01-01', '2026-01-01')",
            (str(_uuid.uuid4()), "https://other-issuer.example"))
        await db.commit()
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="shared-sub", email="x@y.example",
                                 email_verified=True)
    assert resp.status_code == 200
    async with get_db() as db:
        other = await (await db.execute(
            "SELECT role FROM users WHERE oidc_iss='https://other-issuer.example' AND oidc_sub='shared-sub'"
        )).fetchone()
        ours = await (await db.execute(
            "SELECT role FROM users WHERE oidc_iss=? AND oidc_sub='shared-sub'", (ISSUER,)
        )).fetchone()
    assert other["role"] == "admin"   # untouched
    assert ours is not None and ours["role"] == "user"  # fresh, issuer-scoped, NOT admin


@pytest.mark.asyncio
async def test_string_false_email_verified_not_treated_as_verified(oidc_client, rsa_key_and_jwks, httpx_mock):
    # email_verified as the STRING "false" must NOT count as verified (bool("false")
    # is True). The provisioned account must therefore store an EMPTY email.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="strfalse-sub", email="chosen@attacker.example",
                                 email_verified="false")
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT email FROM users WHERE oidc_sub='strfalse-sub'")).fetchone()
    assert (row["email"] or "") == ""  # unverified -> email NOT stored


@pytest.mark.asyncio
async def test_unverified_email_stored_empty(oidc_client, rsa_key_and_jwks, httpx_mock):
    # A brand-new account provisioned from an UNVERIFIED email must have an empty
    # stored email (reverting to unconditional storage would fail this).
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks,
                                 sub="unv-sub", email="unverified@attacker.example",
                                 email_verified=False)
    assert resp.status_code == 200
    from app.database import get_db
    async with get_db() as db:
        row = await (await db.execute(
            "SELECT email FROM users WHERE oidc_sub='unv-sub'")).fetchone()
    assert (row["email"] or "") == ""


# ── Extra required/optional-claim negatives (Codex-named) ────────────────────────

@pytest.mark.asyncio
async def test_rejects_id_token_missing_iat(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, drop_iat=True)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_accepts_id_token_without_at_hash(oidc_client, rsa_key_and_jwks, httpx_mock):
    # at_hash is OPTIONAL — a token omitting it must still be accepted.
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, at_hash=None)
    assert resp.status_code == 200
    assert oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_empty_sub(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, sub="")
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_missing_nonce(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    resp = await _complete_login(oidc_client, httpx_mock, priv_pem, jwks, drop_nonce=True)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_non_string_access_token(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    id_token = _make_id_token(priv_pem, access_token="tok", nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": 12345,  # non-string
                                                 "id_token": id_token, "token_type": "bearer"})
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")


@pytest.mark.asyncio
async def test_rejects_empty_access_token(oidc_client, rsa_key_and_jwks, httpx_mock):
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce, _r, _l = await _start(oidc_client, httpx_mock)
    id_token = _make_id_token(priv_pem, access_token="tok", nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={"access_token": "",  # empty
                                                 "id_token": id_token, "token_type": "bearer"})
    resp = await oidc_client.get(f"/api/auth/oidc/callback?code=abc&state={state}",
                                 follow_redirects=False)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")
