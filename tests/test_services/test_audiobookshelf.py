import pytest
import httpx
from pytest_httpx import HTTPXMock

from app.services.audiobookshelf import AudiobookshelfService

ABS_SETTINGS = {
    "url": "http://abs.local:13378",
    "api_key": "testkey",
    "library_id": ["lib_1"],
}

# A minimal ABS item JSON as the API would return it
ITEM_JSON = {
    "id": "li_abc123",
    "mediaType": "book",
    "media": {
        "metadata": {
            "title": "Project Hail Mary",
            "authorName": "Andy Weir",
            "authors": [{"id": "a1", "name": "Andy Weir"}],
            "narrators": ["Ray Porter"],
            "narratorName": "Ray Porter",
            "series": [{"id": "s1", "name": "Standalone", "sequence": ""}],
            "seriesName": "Standalone",
        },
        "coverPath": "/covers/li_abc123.jpg",
        "tracks": [{"index": 1, "startOffset": 0, "duration": 3600}],
        "numTracks": 1,
        "ebookFile": None,
    },
}

ITEM_NORMALIZED = {
    "abs_id": "li_abc123",
    "abs_url": "http://abs.local:13378/item/li_abc123",
    "title": "Project Hail Mary",
    "author": "Andy Weir",
    "author_items": [{"name": "Andy Weir", "abs_id": "a1"}],
    "series_items": [{"name": "Standalone", "sequence": "", "abs_id": "s1"}],
    "cover_url": "http://abs.local:13378/api/items/li_abc123/cover",
    "narrator": "Ray Porter",
    "formats": [
        {
            "type": "audiobook",
            "narrator": "Ray Porter",
            "abs_id": "li_abc123",
            "abs_url": "http://abs.local:13378/item/li_abc123",
        }
    ],
}


def make_svc():
    return AudiobookshelfService(ABS_SETTINGS)


class TestNormalizeItem:
    def test_audiobook_only(self):
        svc = make_svc()
        result = svc._normalize_item(ITEM_JSON)
        assert result == ITEM_NORMALIZED

    def test_ebook_only(self):
        svc = make_svc()
        item = {
            "id": "li_ebook1",
            "mediaType": "book",
            "media": {
                "metadata": {
                    "title": "Dune",
                    "authorName": "Frank Herbert",
                    "authors": [],
                    "narrators": [],
                    "series": [],
                },
                "coverPath": None,
                "tracks": [],
                "numTracks": 0,
                "ebookFile": {"ino": "1", "metadata": {"filename": "dune.epub"}},
            },
        }
        result = svc._normalize_item(item)
        assert result["formats"] == [{"type": "ebook"}]
        assert result["cover_url"] == ""

    def test_both_formats(self):
        svc = make_svc()
        item = dict(ITEM_JSON)
        item["media"] = dict(ITEM_JSON["media"])
        item["media"]["ebookFile"] = {"ino": "2", "metadata": {"filename": "book.epub"}}
        result = svc._normalize_item(item)
        types = [f["type"] for f in result["formats"]]
        assert "audiobook" in types
        assert "ebook" in types


class TestTestConnection:
    async def test_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries",
            json={"libraries": [{"id": "lib_1", "name": "Audiobooks"}]},
        )
        svc = make_svc()
        result = await svc.test_connection()
        assert result["libraries"] == [{"id": "lib_1", "name": "Audiobooks"}]

    async def test_server_error(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries",
            status_code=401,
        )
        svc = make_svc()
        with pytest.raises(httpx.HTTPStatusError):
            await svc.test_connection()


class TestCheckLibrary:
    async def test_returns_matching_item(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/search?q=Project+Hail+Mary&limit=20",
            json={"book": [{"libraryItem": ITEM_JSON}]},
        )
        svc = make_svc()
        results = await svc.check_library("Project Hail Mary", "Andy Weir")
        assert len(results) == 1
        assert results[0]["title"] == "Project Hail Mary"

    async def test_no_match_returns_empty(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/search?q=Unknown+Book&limit=20",
            json={"book": []},
        )
        svc = make_svc()
        results = await svc.check_library("Unknown Book", "Unknown Author")
        assert results == []

    async def test_server_error_skips_library(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/search?q=Test&limit=20",
            status_code=500,
        )
        svc = make_svc()
        results = await svc.check_library("Test", "Author")
        assert results == []


class TestGetItemById:
    async def test_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/items/li_abc123",
            json=ITEM_JSON,
        )
        svc = make_svc()
        result = await svc.get_item_by_id("li_abc123")
        assert result == ITEM_NORMALIZED

    async def test_not_found(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/items/missing",
            status_code=404,
        )
        svc = make_svc()
        with pytest.raises(httpx.HTTPStatusError):
            await svc.get_item_by_id("missing")


class TestListAllItems:
    async def test_returns_all_items(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/items?limit=0",
            json={"results": [{"id": "li_abc123"}], "total": 1},
        )
        httpx_mock.add_response(
            url="http://abs.local:13378/api/items/li_abc123",
            json=ITEM_JSON,
        )
        svc = make_svc()
        results = await svc.list_all_items()
        assert len(results) == 1
        assert results[0]["abs_id"] == "li_abc123"

    async def test_empty_library(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/items?limit=0",
            json={"results": [], "total": 0},
        )
        svc = make_svc()
        results = await svc.list_all_items()
        assert results == []


class TestScanLibrary:
    async def test_scans_all_configured_libraries(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_1/scan",
            method="POST",
            status_code=200,
        )
        svc = make_svc()
        await svc.scan_library()  # should not raise

    async def test_scans_specific_library(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url="http://abs.local:13378/api/libraries/lib_specific/scan",
            method="POST",
            status_code=200,
        )
        svc = make_svc()
        await svc.scan_library("lib_specific")
