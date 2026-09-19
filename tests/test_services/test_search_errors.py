"""A Hardcover failure must never be reported as an empty result list.

Two production outages looked like "no results" for hours: search_books gathered
its pages with return_exceptions=True and then dropped every non-list with
`if not isinstance(r, list): continue`, so the route answered 200 with
{"results": []} and logged nothing at all.
"""
import asyncio

import httpx
import pytest

from app.services import book_search as bs
from app.services import hardcover as hc


def _resp(status, *, json_body=None, retry_after=None, daily_remaining=None):
    headers = {}
    if retry_after is not None:
        headers["retry-after"] = str(retry_after)
    if daily_remaining is not None:
        headers["x-ratelimit-daily-remaining"] = str(daily_remaining)
    return httpx.Response(
        status, headers=headers,
        json=json_body if json_body is not None else {},
        request=httpx.Request("POST", hc.HC_API_URL),
    )


_HITS = {"data": {"search": {"results": {"hits": []}}}}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr(hc, "_hc_daily_remaining", None)
    monkeypatch.setattr(hc, "_hc_last_request", 0.0)
    monkeypatch.setattr(hc, "_hc_pace_lock", None)
    real = asyncio.sleep
    async def instant(_s): await real(0)
    monkeypatch.setattr(asyncio, "sleep", instant)


class TestSearchBooks:
    @pytest.mark.asyncio
    async def test_rate_limit_raises_rather_than_returning_empty(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(429, retry_after=9843, daily_remaining=0)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        with pytest.raises(hc.HardcoverRateLimited):
            await bs.search_books("Leviathan Wakes", "key")

    @pytest.mark.asyncio
    async def test_total_failure_raises_unavailable(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(500)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        with pytest.raises(bs.HardcoverUnavailable):
            await bs.search_books("Leviathan Wakes", "key")

    @pytest.mark.asyncio
    async def test_partial_failure_still_returns_the_pages_that_worked(self, monkeypatch):
        calls = {"n": 0}

        async def fake_post(self, url, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                return _resp(500)
            return _resp(200, json_body={"data": {"search": {"results": {"hits": [
                {"document": {"id": calls["n"], "title": "T", "users_count": 1}}
            ]}}}})
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        out = await bs.search_books("q", "key", pages=3)
        assert len(out) >= 1, "one bad page must not discard the good ones"

    @pytest.mark.asyncio
    async def test_genuine_no_matches_is_still_an_empty_list(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(200, json_body=_HITS)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        assert await bs.search_books("asdkjhasd", "key") == []

    @pytest.mark.asyncio
    async def test_no_api_key_is_not_an_upstream_error(self):
        assert await bs.search_books("q", "") == []


class TestSingleFetchers:
    @pytest.mark.asyncio
    async def test_series_books_raises_on_failure(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(500)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(bs.HardcoverUnavailable):
            await bs.get_hc_series_books("123", "key")

    @pytest.mark.asyncio
    async def test_author_books_propagates_rate_limit(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(429, retry_after=60, daily_remaining=0)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        with pytest.raises(hc.HardcoverRateLimited):
            await bs.get_hc_author_books("123", "key")


class TestRouteContract:
    """The route must answer with `error` set, not a bare empty list."""

    @pytest.mark.asyncio
    async def test_helper_maps_rate_limit_to_a_message(self):
        from app.routes.books import _hc_results_or_error

        async def boom():
            raise hc.HardcoverRateLimited("daily", retry_after=9843)

        results, error = await _hc_results_or_error(boom())
        assert results == []
        assert error and "rate limited" in error.lower()

    @pytest.mark.asyncio
    async def test_helper_maps_unavailable_to_a_message(self):
        from app.routes.books import _hc_results_or_error

        async def boom():
            raise bs.HardcoverUnavailable("connection refused")

        results, error = await _hc_results_or_error(boom())
        assert results == []
        assert error and "could not be reached" in error.lower()

    @pytest.mark.asyncio
    async def test_success_passes_through_with_no_error(self):
        from app.routes.books import _hc_results_or_error

        async def ok():
            return [{"title": "A Book"}]

        results, error = await _hc_results_or_error(ok())
        assert error is None and results == [{"title": "A Book"}]
