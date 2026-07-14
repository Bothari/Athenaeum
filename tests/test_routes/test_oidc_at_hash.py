"""Regression test for the OIDC at_hash login failure (issue #1).

Providers such as Authelia put an at_hash claim in the ID token. python-jose
verifies at_hash against the access token and raises "No access_token provided
to compare against at_hash claim" when it is not supplied, which broke every
OIDC login. oidc_callback must pass the access token to jwt.decode.
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
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"
AUTH_URL = f"{ISSUER}/authorize"
TOKEN_URL = f"{ISSUER}/token"
JWKS_URL = f"{ISSUER}/jwks"

DISCOVERY_DOC = {
    "issuer": ISSUER,
    "authorization_endpoint": AUTH_URL,
    "token_endpoint": TOKEN_URL,
    "jwks_uri": JWKS_URL,
}

_OIDC_AUTH = {
    "oidc_enabled": True,
    "oidc_provider_url": ISSUER,
    "oidc_client_id": CLIENT_ID,
    "oidc_client_secret": "client-secret",
    "oidc_scopes": "openid email profile",
    "session_secret": "test-session-secret",
    "session_days": 30,
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
    # OIDC: base64url(left-most half of SHA-256(access_token)) for an RS256 id_token.
    return _b64u(hashlib.sha256(access_token.encode()).digest()[:16])


def _make_id_token(priv_pem, *, access_token, nonce, at_hash=None):
    now = int(time.time())
    claims = {
        "iss": ISSUER, "sub": "user-sub-1", "aud": CLIENT_ID,
        "email": "reader@example.com", "nonce": nonce,
        "iat": now, "exp": now + 300,
        "at_hash": at_hash if at_hash is not None else _at_hash(access_token),
    }
    return jose_jwt.encode(claims, priv_pem, algorithm="RS256", headers={"kid": "test"})


@pytest_asyncio.fixture
async def oidc_client(db_path, tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(tmp_path / "settings.yaml"))
    auth_routes._oidc_discovery_cache.clear()
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="https://test") as c:
        # public_url must be set so redirect_uri is absolute (issue #2 is separate).
        await c.put("/api/settings", json={
            "auth": dict(_OIDC_AUTH),
            "general": {"public_url": "https://test"},
        })
        yield c


async def _start(client, httpx_mock):
    # Drive /start; read state+nonce from the authorize redirect. The oidc_state
    # cookie is persisted by the client's cookie jar and replayed on the callback.
    httpx_mock.add_response(url=DISCOVERY_URL, json=DISCOVERY_DOC)
    resp = await client.get("/api/auth/oidc/start", follow_redirects=False)
    assert resp.status_code == 302
    q = parse_qs(urlparse(resp.headers["location"]).query)
    return q["state"][0], q["nonce"][0]


@pytest.mark.asyncio
async def test_login_succeeds_when_id_token_has_at_hash(oidc_client, rsa_key_and_jwks, httpx_mock):
    """A valid id_token carrying an at_hash claim must be accepted.

    Before the fix, jwt.decode received no access_token and raised
    "No access_token provided to compare against at_hash claim" -> HTTP 400.
    """
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce = await _start(oidc_client, httpx_mock)
    access_token = "an-access-token"
    id_token = _make_id_token(priv_pem, access_token=access_token, nonce=nonce)
    httpx_mock.add_response(url=TOKEN_URL, json={
        "access_token": access_token, "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)

    resp = await oidc_client.get(
        f"/api/auth/oidc/callback?code=abc&state={state}", follow_redirects=False)
    assert resp.status_code == 200, resp.text
    assert oidc_client.cookies.get("session")  # session issued


@pytest.mark.asyncio
async def test_at_hash_is_actually_verified(oidc_client, rsa_key_and_jwks, httpx_mock):
    """An id_token whose at_hash does not match the access token must be rejected.

    This guards against a "fix" that silently disables at_hash verification: the
    access token must be passed AND checked.
    """
    priv_pem, jwks = rsa_key_and_jwks
    state, nonce = await _start(oidc_client, httpx_mock)
    access_token = "an-access-token"
    id_token = _make_id_token(
        priv_pem, access_token=access_token, nonce=nonce,
        at_hash=_at_hash("a-different-token"))
    httpx_mock.add_response(url=TOKEN_URL, json={
        "access_token": access_token, "id_token": id_token, "token_type": "bearer"})
    httpx_mock.add_response(url=JWKS_URL, json=jwks)

    resp = await oidc_client.get(
        f"/api/auth/oidc/callback?code=abc&state={state}", follow_redirects=False)
    assert resp.status_code == 400
    assert not oidc_client.cookies.get("session")
