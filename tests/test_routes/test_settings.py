import pytest
from httpx import AsyncClient, ASGITransport
from pytest_httpx import HTTPXMock

from app.main import app
from app import settings as settings_module


@pytest.fixture
async def client(db_path, tmp_path, monkeypatch):
    settings_path = str(tmp_path / "settings.yaml")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestGetSettings:
    async def test_returns_defaults_when_no_file(self, client):
        resp = await client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "audiobookshelf" in data
        assert "prowlarr" in data
        assert "general" in data

    async def test_masks_sensitive_fields(self, client):
        # Save a real api_key first
        await client.put("/api/settings", json={"prowlarr": {"api_key": "realkey"}})
        resp = await client.get("/api/settings")
        assert resp.status_code == 200
        assert resp.json()["prowlarr"]["api_key"] == "********"

    async def test_empty_sensitive_fields_not_masked(self, client):
        resp = await client.get("/api/settings")
        assert resp.status_code == 200
        # Empty strings should not be masked
        assert resp.json()["prowlarr"]["api_key"] == ""


class TestPutSettings:
    async def test_saves_and_reloads(self, client):
        resp = await client.put(
            "/api/settings",
            json={"audiobookshelf": {"url": "http://abs.local:13378"}},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

        get_resp = await client.get("/api/settings")
        assert get_resp.json()["audiobookshelf"]["url"] == "http://abs.local:13378"

    async def test_rejects_unknown_section(self, client):
        resp = await client.put("/api/settings", json={"unknown_section": {"foo": "bar"}})
        assert resp.status_code == 400
        assert "Unknown" in resp.json()["detail"]

    async def test_sentinel_does_not_overwrite(self, client):
        # Store a real value
        await client.put("/api/settings", json={"prowlarr": {"api_key": "secret123"}})
        # PUT with sentinel — should leave secret123 intact
        await client.put("/api/settings", json={"prowlarr": {"api_key": "********", "url": "http://p.local"}})
        # Read raw settings to confirm value wasn't overwritten
        raw = await settings_module.get_settings()
        assert raw["prowlarr"]["api_key"] == "secret123"
        assert raw["prowlarr"]["url"] == "http://p.local"

    async def test_rejects_invalid_cron(self, client):
        resp = await client.put(
            "/api/settings",
            json={"schedule": {"library_sync": "not a cron"}},
        )
        assert resp.status_code == 400
        assert "cron" in resp.json()["detail"].lower()

    async def test_accepts_valid_cron(self, client):
        resp = await client.put(
            "/api/settings",
            json={"schedule": {"library_sync": "0 2 * * *"}},
        )
        assert resp.status_code == 200

    async def test_deep_merge_preserves_existing(self, client):
        # Set two fields
        await client.put("/api/settings", json={"hardcover": {"api_key": "hckey", "preferred_language": "English"}})
        # Update only one
        await client.put("/api/settings", json={"hardcover": {"preferred_language": "German"}})
        raw = await settings_module.get_settings()
        assert raw["hardcover"]["api_key"] == "hckey"
        assert raw["hardcover"]["preferred_language"] == "German"


class TestTestAbs:
    async def test_success(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"audiobookshelf": {"url": "http://abs.local:13378", "api_key": "key"}},
        )
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries",
            json={"libraries": [{"id": "lib_1", "name": "Audiobooks"}]},
        )
        resp = await client.post("/api/settings/test/abs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["libraries"]) == 1
        assert data["libraries"][0]["id"] == "lib_1"

    async def test_not_configured_returns_400(self, client):
        resp = await client.post("/api/settings/test/abs")
        assert resp.status_code == 400

    async def test_connection_failure_returns_502(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"audiobookshelf": {"url": "http://abs.local:13378", "api_key": "key"}},
        )
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries",
            status_code=401,
        )
        resp = await client.post("/api/settings/test/abs")
        assert resp.status_code == 502


class TestTestProwlarr:
    async def test_not_configured_returns_400(self, client):
        resp = await client.post("/api/settings/test/prowlarr")
        assert resp.status_code == 400

    async def test_success(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"prowlarr": {"url": "http://prowlarr.local", "api_key": "pkey"}},
        )
        httpx_mock.add_response(
            url="http://prowlarr.local/api/v1/system/status",
            json={"version": "1.12.0"},
        )
        resp = await client.post("/api/settings/test/prowlarr")
        assert resp.status_code == 200
        assert resp.json()["version"] == "1.12.0"

    async def test_failure_returns_502(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"prowlarr": {"url": "http://prowlarr.local", "api_key": "bad"}},
        )
        httpx_mock.add_response(
            url="http://prowlarr.local/api/v1/system/status",
            status_code=403,
        )
        resp = await client.post("/api/settings/test/prowlarr")
        assert resp.status_code == 502


class TestTestSabnzbd:
    async def test_not_configured_returns_400(self, client):
        resp = await client.post("/api/settings/test/sabnzbd")
        assert resp.status_code == 400

    async def test_success(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"sabnzbd": {"url": "http://sabnzbd.local", "api_key": "sbkey"}},
        )
        httpx_mock.add_response(
            url="http://sabnzbd.local/api?mode=version&output=json&apikey=sbkey",
            json={"version": "4.2.0"},
        )
        resp = await client.post("/api/settings/test/sabnzbd")
        assert resp.status_code == 200
        assert resp.json()["version"] == "4.2.0"


class TestTestHardcover:
    async def test_not_configured_returns_400(self, client):
        resp = await client.post("/api/settings/test/hardcover")
        assert resp.status_code == 400

    async def test_success(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"hardcover": {"api_key": "hckey"}},
        )
        # Hardcover returns me as an array
        httpx_mock.add_response(
            url="https://api.hardcover.app/v1/graphql",
            json={"data": {"me": [{"id": 1, "username": "testuser"}]}},
        )
        resp = await client.post("/api/settings/test/hardcover")
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_auth_failure_returns_502(self, client, httpx_mock: HTTPXMock):
        await client.put(
            "/api/settings",
            json={"hardcover": {"api_key": "badkey"}},
        )
        httpx_mock.add_response(
            url="https://api.hardcover.app/v1/graphql",
            json={"data": {"me": []}},
        )
        resp = await client.post("/api/settings/test/hardcover")
        assert resp.status_code == 502


class TestTestWithUnsavedValues:
    """Test that body values are used without requiring a prior save."""

    async def test_prowlarr_uses_body_url_without_save(self, client, httpx_mock: HTTPXMock):
        # No settings saved at all — values come entirely from the request body
        httpx_mock.add_response(
            url="http://prowlarr.unsaved/api/v1/system/status",
            json={"version": "2.0.0"},
        )
        resp = await client.post(
            "/api/settings/test/prowlarr",
            json={"url": "http://prowlarr.unsaved", "api_key": "newkey"},
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "2.0.0"

    async def test_sabnzbd_uses_body_url_without_save(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://sabnzbd.unsaved/api?mode=version&output=json&apikey=newkey",
            json={"version": "5.0.0"},
        )
        resp = await client.post(
            "/api/settings/test/sabnzbd",
            json={"url": "http://sabnzbd.unsaved", "api_key": "newkey"},
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == "5.0.0"

    async def test_sentinel_falls_back_to_saved_value(self, client, httpx_mock: HTTPXMock):
        # Save a real api_key, then test with a new URL but sentinel for the key
        await client.put(
            "/api/settings",
            json={"prowlarr": {"url": "http://old.local", "api_key": "savedkey"}},
        )
        httpx_mock.add_response(
            url="http://prowlarr.new/api/v1/system/status",
            json={"version": "2.0.0"},
        )
        # Send new URL but "********" for key — backend should use saved "savedkey"
        resp = await client.post(
            "/api/settings/test/prowlarr",
            json={"url": "http://prowlarr.new", "api_key": "********"},
        )
        assert resp.status_code == 200
        # Verify the request was made with the saved key (httpx_mock matched the URL,
        # meaning the new URL was used; if the key were wrong the mock still matches —
        # but the key resolution logic is in _merge_with_saved which we test directly below)

    async def test_merge_with_saved_strips_sentinel(self, client):
        from app.routes.settings import _merge_with_saved
        saved = {"url": "http://old", "api_key": "secret"}
        result = _merge_with_saved(saved, {"url": "http://new", "api_key": "********"})
        assert result["url"] == "http://new"
        assert result["api_key"] == "secret"

    async def test_merge_with_saved_overrides_non_sentinel(self, client):
        from app.routes.settings import _merge_with_saved
        saved = {"url": "http://old", "api_key": "secret"}
        result = _merge_with_saved(saved, {"url": "http://new", "api_key": "newkey"})
        assert result["url"] == "http://new"
        assert result["api_key"] == "newkey"
