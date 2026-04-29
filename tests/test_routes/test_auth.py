import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from passlib.context import CryptContext

from app.main import app
from app import settings as settings_module
from app.auth import _make_session_token
from app.database import get_db

SECRET = "test-secret"
DAYS = 30
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture
async def anon_client(db_path, tmp_path, monkeypatch):
    """Client with auth fully disabled (default state)."""
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(db_path, tmp_path, monkeypatch):
    """Client with form auth enabled and a known session secret."""
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # Auth is initially disabled, so this PUT goes through as passthrough.
        await c.put("/api/settings", json={
            "auth": {"form_enabled": True, "session_secret": SECRET, "session_days": DAYS}
        })
        yield c


def _token(user_id: str, role: str) -> str:
    return _make_session_token(user_id, role, SECRET, DAYS)


async def _insert_user(
    username: str,
    role: str,
    password: str = "pass123",
    force_change: bool = False,
) -> str:
    uid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    ph = _pwd.hash(password)
    async with get_db() as db:
        await db.execute(
            """INSERT INTO users
               (id, username, password_hash, role, force_password_change, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (uid, username, ph, role, int(force_change), now, now),
        )
        await db.commit()
    return uid


async def _insert_book(title: str = "Test Book") -> str:
    bid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await db.execute(
            "INSERT INTO books (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (bid, title, now, now),
        )
        await db.commit()
    return bid


# ── Auth disabled passthrough ─────────────────────────────────────────────────

class TestAuthPassthrough:
    """With auth disabled all routes work without credentials."""

    async def test_books_accessible_without_cookie(self, anon_client):
        resp = await anon_client.get("/api/books")
        assert resp.status_code == 200

    async def test_me_returns_anonymous_admin(self, anon_client):
        resp = await anon_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "anonymous"
        assert data["role"] == "admin"

    async def test_settings_accessible_without_cookie(self, anon_client):
        resp = await anon_client.get("/api/settings")
        assert resp.status_code == 200


# ── require_auth ──────────────────────────────────────────────────────────────

class TestRequireAuth:
    """require_auth blocks requests when form auth is enabled."""

    async def test_no_cookie_returns_401(self, auth_client):
        resp = await auth_client.get("/api/books")
        assert resp.status_code == 401

    async def test_bad_token_returns_401(self, auth_client):
        resp = await auth_client.get("/api/books", cookies={"session": "not-a-jwt"})
        assert resp.status_code == 401

    async def test_valid_admin_token_passes(self, auth_client):
        uid = await _insert_user("authadm", "admin")
        resp = await auth_client.get("/api/books", cookies={"session": _token(uid, "admin")})
        assert resp.status_code == 200

    async def test_valid_user_token_passes(self, auth_client):
        uid = await _insert_user("authusr", "user")
        resp = await auth_client.get("/api/books", cookies={"session": _token(uid, "user")})
        assert resp.status_code == 200


# ── require_admin ─────────────────────────────────────────────────────────────

class TestRequireAdmin:
    """require_admin rejects non-admin roles with 403."""

    async def test_user_role_forbidden_on_settings(self, auth_client):
        uid = await _insert_user("admchk_usr", "user")
        resp = await auth_client.get("/api/settings", cookies={"session": _token(uid, "user")})
        assert resp.status_code == 403

    async def test_admin_role_allowed_on_settings(self, auth_client):
        uid = await _insert_user("admchk_adm", "admin")
        resp = await auth_client.get("/api/settings", cookies={"session": _token(uid, "admin")})
        assert resp.status_code == 200


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    async def test_login_rejected_when_form_disabled(self, anon_client):
        resp = await anon_client.post("/api/auth/login", json={"username": "x", "password": "y"})
        assert resp.status_code == 400

    async def test_login_wrong_username_returns_401(self, auth_client):
        resp = await auth_client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    async def test_login_wrong_password_returns_401(self, auth_client):
        await _insert_user("lgtest1", "admin", password="correct")
        resp = await auth_client.post("/api/auth/login", json={"username": "lgtest1", "password": "wrong"})
        assert resp.status_code == 401

    async def test_login_valid_credentials(self, auth_client):
        await _insert_user("lgtest2", "admin", password="mypass")
        resp = await auth_client.post("/api/auth/login", json={"username": "lgtest2", "password": "mypass"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["role"] == "admin"
        assert data["username"] == "lgtest2"

    async def test_login_sets_session_cookie(self, auth_client):
        await _insert_user("lgtest3", "user", password="pw")
        resp = await auth_client.post("/api/auth/login", json={"username": "lgtest3", "password": "pw"})
        assert resp.status_code == 200
        assert resp.cookies.get("session") is not None

    async def test_login_reports_force_password_change(self, auth_client):
        await _insert_user("lgtest4", "user", password="pw", force_change=True)
        resp = await auth_client.post("/api/auth/login", json={"username": "lgtest4", "password": "pw"})
        assert resp.status_code == 200
        assert resp.json()["force_password_change"] is True


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    async def test_logout_returns_ok(self, auth_client):
        uid = await _insert_user("logout1", "admin")
        resp = await auth_client.post("/api/auth/logout", cookies={"session": _token(uid, "admin")})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


# ── Me ────────────────────────────────────────────────────────────────────────

class TestMe:
    async def test_me_auth_disabled(self, anon_client):
        resp = await anon_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "anonymous"
        assert data["role"] == "admin"

    async def test_me_no_cookie_returns_401(self, auth_client):
        resp = await auth_client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_me_returns_user_info(self, auth_client):
        uid = await _insert_user("metest1", "user")
        resp = await auth_client.get("/api/auth/me", cookies={"session": _token(uid, "user")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "metest1"
        assert data["role"] == "user"
        assert data["user_id"] == uid


# ── Change password ───────────────────────────────────────────────────────────

class TestChangePassword:
    async def test_wrong_current_password_returns_401(self, auth_client):
        uid = await _insert_user("cptest1", "user", password="oldpass")
        resp = await auth_client.post(
            "/api/auth/change-password",
            json={"current_password": "wrong", "new_password": "newpass"},
            cookies={"session": _token(uid, "user")},
        )
        assert resp.status_code == 401

    async def test_change_password_success(self, auth_client):
        uid = await _insert_user("cptest2", "user", password="oldpass", force_change=True)
        resp = await auth_client.post(
            "/api/auth/change-password",
            json={"current_password": "oldpass", "new_password": "newpass"},
            cookies={"session": _token(uid, "user")},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_change_password_clears_force_change_flag(self, auth_client):
        uid = await _insert_user("cptest3", "user", password="oldpass", force_change=True)
        await auth_client.post(
            "/api/auth/change-password",
            json={"current_password": "oldpass", "new_password": "newpass"},
            cookies={"session": _token(uid, "user")},
        )
        async with get_db() as db:
            row = await (await db.execute(
                "SELECT force_password_change FROM users WHERE id=?", (uid,)
            )).fetchone()
        assert row["force_password_change"] == 0

    async def test_new_password_works_after_change(self, auth_client):
        await _insert_user("cptest4", "user", password="oldpass")
        uid = await _insert_user("cptest4b", "user", password="oldpass")
        # find the second one
        async with get_db() as db:
            row = await (await db.execute("SELECT id FROM users WHERE username='cptest4b'")).fetchone()
        uid = row["id"]
        await auth_client.post(
            "/api/auth/change-password",
            json={"current_password": "oldpass", "new_password": "newpass"},
            cookies={"session": _token(uid, "user")},
        )
        resp = await auth_client.post("/api/auth/login", json={"username": "cptest4b", "password": "newpass"})
        assert resp.status_code == 200


# ── User management ───────────────────────────────────────────────────────────

class TestUserManagement:
    async def test_list_users_requires_admin(self, auth_client):
        uid = await _insert_user("umlst_usr", "user")
        resp = await auth_client.get("/api/users", cookies={"session": _token(uid, "user")})
        assert resp.status_code == 403

    async def test_list_users_as_admin(self, auth_client):
        uid = await _insert_user("umlst_adm", "admin")
        resp = await auth_client.get("/api/users", cookies={"session": _token(uid, "admin")})
        assert resp.status_code == 200
        assert "users" in resp.json()

    async def test_create_user_as_admin(self, auth_client):
        adm = await _insert_user("umcr_adm", "admin")
        resp = await auth_client.post(
            "/api/users",
            json={"username": "umcr_new", "password": "pw123", "role": "user"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "umcr_new"
        assert data["role"] == "user"
        assert data["force_password_change"] is True

    async def test_create_user_requires_admin(self, auth_client):
        uid = await _insert_user("umcr_usr", "user")
        resp = await auth_client.post(
            "/api/users",
            json={"username": "umcr_blocked", "password": "pw"},
            cookies={"session": _token(uid, "user")},
        )
        assert resp.status_code == 403

    async def test_create_user_duplicate_username_returns_409(self, auth_client):
        adm = await _insert_user("umdup_adm", "admin")
        await _insert_user("umdup_existing", "user")
        resp = await auth_client.post(
            "/api/users",
            json={"username": "umdup_existing", "password": "pw"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 409

    async def test_create_user_invalid_role_returns_400(self, auth_client):
        adm = await _insert_user("umrole_adm", "admin")
        resp = await auth_client.post(
            "/api/users",
            json={"username": "umrole_bad", "password": "pw", "role": "superuser"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 400

    async def test_patch_user_role(self, auth_client):
        adm = await _insert_user("umpatch_adm", "admin")
        target = await _insert_user("umpatch_target", "user")
        resp = await auth_client.patch(
            f"/api/users/{target}",
            json={"role": "admin"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        async with get_db() as db:
            row = await (await db.execute("SELECT role FROM users WHERE id=?", (target,))).fetchone()
        assert row["role"] == "admin"

    async def test_patch_unknown_user_returns_404(self, auth_client):
        adm = await _insert_user("umpatch404_adm", "admin")
        resp = await auth_client.patch(
            f"/api/users/{uuid.uuid4()}",
            json={"role": "user"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 404

    async def test_delete_user(self, auth_client):
        adm = await _insert_user("umdel_adm", "admin")
        target = await _insert_user("umdel_target", "user")
        resp = await auth_client.delete(
            f"/api/users/{target}",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        async with get_db() as db:
            row = await (await db.execute("SELECT id FROM users WHERE id=?", (target,))).fetchone()
        assert row is None

    async def test_delete_self_returns_400(self, auth_client):
        adm = await _insert_user("umself_adm", "admin")
        resp = await auth_client.delete(
            f"/api/users/{adm}",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 400

    async def test_delete_unknown_user_returns_404(self, auth_client):
        adm = await _insert_user("umdel404_adm", "admin")
        resp = await auth_client.delete(
            f"/api/users/{uuid.uuid4()}",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 404

    async def test_reset_password_sets_force_change(self, auth_client):
        adm = await _insert_user("umreset_adm", "admin")
        target = await _insert_user("umreset_target", "user", force_change=False)
        resp = await auth_client.post(
            f"/api/users/{target}/reset-password",
            json={"new_password": "newpw"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        async with get_db() as db:
            row = await (await db.execute(
                "SELECT force_password_change FROM users WHERE id=?", (target,)
            )).fetchone()
        assert row["force_password_change"] == 1

    async def test_reset_password_unknown_user_returns_404(self, auth_client):
        adm = await _insert_user("umreset404_adm", "admin")
        resp = await auth_client.post(
            f"/api/users/{uuid.uuid4()}/reset-password",
            json={"new_password": "pw"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 404


# ── Pending request flow ──────────────────────────────────────────────────────

class TestPendingRequests:
    async def test_admin_request_lands_as_requested(self, auth_client):
        adm = await _insert_user("preq_adm", "admin")
        book_id = await _insert_book()
        resp = await auth_client.post(
            "/api/requests",
            json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "requested"

    async def test_user_request_lands_as_pending(self, auth_client):
        uid = await _insert_user("preq_usr", "user")
        book_id = await _insert_book()
        resp = await auth_client.post(
            "/api/requests",
            json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(uid, "user")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_user_sees_only_own_requests(self, auth_client):
        uid1 = await _insert_user("preq_own", "user")
        uid2 = await _insert_user("preq_other", "user")
        b1 = await _insert_book("Book A")
        b2 = await _insert_book("Book B")

        await auth_client.post(
            "/api/requests", json={"book_id": b1, "type": "ebook"},
            cookies={"session": _token(uid1, "user")},
        )
        await auth_client.post(
            "/api/requests", json={"book_id": b2, "type": "ebook"},
            cookies={"session": _token(uid2, "user")},
        )

        resp = await auth_client.get("/api/requests", cookies={"session": _token(uid1, "user")})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["requested_by_user_id"] == uid1

    async def test_pending_list_requires_admin(self, auth_client):
        uid = await _insert_user("pend_notadm", "user")
        resp = await auth_client.get("/api/requests/pending", cookies={"session": _token(uid, "user")})
        assert resp.status_code == 403

    async def test_pending_list_returns_pending_requests(self, auth_client):
        adm = await _insert_user("pend_adm", "admin")
        uid = await _insert_user("pend_usr", "user")
        book_id = await _insert_book()

        await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(uid, "user")},
        )

        resp = await auth_client.get(
            "/api/requests/pending", cookies={"session": _token(adm, "admin")}
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    async def test_admin_requests_not_in_pending_list(self, auth_client):
        adm = await _insert_user("pend_admonly", "admin")
        book_id = await _insert_book()

        await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(adm, "admin")},
        )

        resp = await auth_client.get(
            "/api/requests/pending", cookies={"session": _token(adm, "admin")}
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 0

    async def test_approve_pending_request(self, auth_client):
        adm = await _insert_user("appr_adm", "admin")
        uid = await _insert_user("appr_usr", "user")
        book_id = await _insert_book()

        req_resp = await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(uid, "user")},
        )
        req_id = req_resp.json()["id"]

        resp = await auth_client.post(
            f"/api/requests/{req_id}/approve",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "requested"

    async def test_reject_pending_request(self, auth_client):
        adm = await _insert_user("rej_adm", "admin")
        uid = await _insert_user("rej_usr", "user")
        book_id = await _insert_book()

        req_resp = await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(uid, "user")},
        )
        req_id = req_resp.json()["id"]

        resp = await auth_client.post(
            f"/api/requests/{req_id}/reject",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    async def test_approve_nonpending_request_returns_400(self, auth_client):
        adm = await _insert_user("appr_np_adm", "admin")
        book_id = await _insert_book()

        req_resp = await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(adm, "admin")},
        )
        req_id = req_resp.json()["id"]
        # Status is 'requested', not 'pending'

        resp = await auth_client.post(
            f"/api/requests/{req_id}/approve",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 400

    async def test_reject_nonpending_request_returns_400(self, auth_client):
        adm = await _insert_user("rej_np_adm", "admin")
        book_id = await _insert_book()

        req_resp = await auth_client.post(
            "/api/requests", json={"book_id": book_id, "type": "ebook"},
            cookies={"session": _token(adm, "admin")},
        )
        req_id = req_resp.json()["id"]

        resp = await auth_client.post(
            f"/api/requests/{req_id}/reject",
            cookies={"session": _token(adm, "admin")},
        )
        assert resp.status_code == 400
