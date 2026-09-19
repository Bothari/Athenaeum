"""Rate-limit handling for Hardcover.

These cover the failure that took production search down twice: background
metadata refresh retried 429s per book, and since a rejected request still
counts against the quota, it consumed the entire daily allowance and left
interactive search with nothing.
"""
import asyncio
import time

import httpx
import pytest

from app.services import hardcover as hc
from app.services import library_sync as ls


_real_sleep = asyncio.sleep


async def _instant_sleep(_seconds):
    """Drop the pacing delay without recursing into the patched sleep."""
    await _real_sleep(0)


def _resp(status: int, *, daily_remaining=None, retry_after=None, json_body=None) -> httpx.Response:
    headers = {}
    if daily_remaining is not None:
        headers["x-ratelimit-daily-remaining"] = str(daily_remaining)
    if retry_after is not None:
        headers["retry-after"] = str(retry_after)
    return httpx.Response(
        status, headers=headers, json=json_body if json_body is not None else {"data": {}},
        request=httpx.Request("POST", hc.HC_API_URL),
    )


@pytest.fixture(autouse=True)
def _reset_quota():
    hc._hc_daily_remaining = None
    yield
    hc._hc_daily_remaining = None


class TestHcPost:
    @pytest.mark.asyncio
    async def test_429_raises_rate_limited_not_http_error(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(429, retry_after=9843, daily_remaining=0)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        with pytest.raises(ls.HardcoverRateLimited) as ei:
            await ls.hc_post("q", {}, "key")
        assert ei.value.retry_after == 9843

    @pytest.mark.asyncio
    async def test_records_daily_remaining_from_headers(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(200, daily_remaining=4321, json_body={"data": {"ok": True}})
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        await ls.hc_post("q", {}, "key")
        assert ls.hc_daily_remaining() == 4321

    @pytest.mark.asyncio
    async def test_background_call_refused_at_the_reserve(self, monkeypatch):
        """Background work must yield before the quota is gone, so a user
        searching still has budget to spend."""
        calls = []

        async def fake_post(self, url, **kw):
            calls.append(url)
            return _resp(200, daily_remaining=ls.HC_DAILY_RESERVE)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        await ls.hc_post("q", {}, "key")           # observes the low allowance
        assert len(calls) == 1
        with pytest.raises(ls.HardcoverRateLimited):
            await ls.hc_post("q", {}, "key")       # next background call refused
        assert len(calls) == 1, "refusal must not reach the network"

    @pytest.mark.asyncio
    async def test_interactive_call_may_spend_the_reserve(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(200, daily_remaining=1)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        await ls.hc_post("q", {}, "key")
        await ls.hc_post("q", {}, "key", background=False)  # must not raise


class TestFetchBookMeta:
    @pytest.mark.asyncio
    async def test_429_is_not_retried(self, monkeypatch):
        """The regression: this used to fire five requests per book."""
        calls = []

        async def fake_post(self, url, **kw):
            calls.append(url)
            return _resp(429, retry_after=9843, daily_remaining=0)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        with pytest.raises(ls.HardcoverRateLimited):
            await ls._fetch_hc_book_meta(123, "key")
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_other_errors_still_return_empty(self, monkeypatch):
        async def fake_post(self, url, **kw):
            return _resp(500)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        assert await ls._fetch_hc_book_meta(123, "key") == {}


class TestWaitOrAbort:
    @pytest.mark.asyncio
    async def test_short_throttle_is_waited_out(self, monkeypatch):
        slept = []

        async def fake_sleep(s):
            slept.append(s)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        await ls._hc_wait_or_abort(ls.HardcoverRateLimited("per-minute", retry_after=8), time.monotonic() + 3600)
        assert slept == [8]

    @pytest.mark.asyncio
    async def test_daily_quota_aborts(self):
        exc = ls.HardcoverRateLimited("daily", retry_after=9843)
        with pytest.raises(ls.HardcoverRateLimited):
            await ls._hc_wait_or_abort(exc, time.monotonic() + 3600)

    @pytest.mark.asyncio
    async def test_wait_past_the_deadline_aborts(self):
        exc = ls.HardcoverRateLimited("per-minute", retry_after=30)
        with pytest.raises(ls.HardcoverRateLimited):
            await ls._hc_wait_or_abort(exc, time.monotonic() + 5)

    @pytest.mark.asyncio
    async def test_reserve_refusal_has_no_retry_after_and_aborts(self):
        exc = ls.HardcoverRateLimited("reserve reached")
        with pytest.raises(ls.HardcoverRateLimited):
            await ls._hc_wait_or_abort(exc, time.monotonic() + 3600)


class TestRateLimitedLoop:
    @pytest.mark.asyncio
    async def test_daily_limit_stops_the_loop_and_counts_the_rest_skipped(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _instant_sleep)
        seen = []

        async def fn(item):
            seen.append(item)
            if item == 2:
                raise ls.HardcoverRateLimited("daily", retry_after=9843)
            return True

        with pytest.raises(ls.HardcoverRateLimited):
            await ls._hc_rate_limited_loop([1, 2, 3, 4], fn, time.monotonic() + 3600)
        assert seen == [1, 2], "must not keep spending quota after the daily limit"

    @pytest.mark.asyncio
    async def test_deadline_stops_the_loop(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _instant_sleep)
        seen = []

        async def fn(item):
            seen.append(item)
            return True

        out = await ls._hc_rate_limited_loop([1, 2, 3], fn, time.monotonic() - 1)
        assert seen == []
        assert out["skipped"] == 3


class TestRequestPacing:
    """Pacing must be per REQUEST, not per item.

    One linking item fans out to four requests, so pacing per item ran at roughly
    200 requests/min against a 60/min ceiling — it sat permanently in per-minute
    throttling, burning quota on rejections while barely progressing.
    """

    @pytest.mark.asyncio
    async def test_hc_post_paces_every_request(self, monkeypatch):
        waits = []

        async def fake_sleep(s):
            waits.append(s)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        monkeypatch.setattr(hc, "_hc_last_request", 0.0)
        monkeypatch.setattr(hc, "_hc_pace_lock", None)

        async def fake_post(self, url, **kw):
            return _resp(200, daily_remaining=4000)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

        await ls.hc_post("q", {}, "k")
        await ls.hc_post("q", {}, "k")   # immediately after: must be made to wait
        assert any(w > 0 for w in waits), "second request was not paced"

    @pytest.mark.asyncio
    async def test_concurrent_requests_are_serialised(self, monkeypatch):
        """The four-page fan-out must not all leave at once."""
        monkeypatch.setattr(hc, "_hc_last_request", 0.0)
        monkeypatch.setattr(hc, "_hc_pace_lock", None)
        in_flight = {"now": 0, "max": 0}

        async def fake_post(self, url, **kw):
            in_flight["now"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["now"])
            await _real_sleep(0)
            in_flight["now"] -= 1
            return _resp(200, daily_remaining=4000)
        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        monkeypatch.setattr(asyncio, "sleep", _instant_sleep)

        await asyncio.gather(*[ls.hc_post("q", {}, "k") for _ in range(4)])
        assert in_flight["max"] == 1, "requests must be serialised by the pacer"


class TestThrottleRetryCap:
    @pytest.mark.asyncio
    async def test_permanently_throttled_item_is_abandoned(self, monkeypatch):
        """The regression: an unbounded re-queue fired ~170 attempts at 3 books."""
        monkeypatch.setattr(asyncio, "sleep", _instant_sleep)
        attempts = {"n": 0}

        async def fn(item):
            attempts["n"] += 1
            raise ls.HardcoverRateLimited("per-minute", retry_after=2)

        out = await ls._hc_rate_limited_loop([1], fn, time.monotonic() + 3600)
        assert attempts["n"] == ls.HC_MAX_THROTTLE_RETRIES
        assert out["failed"] == 1

    @pytest.mark.asyncio
    async def test_item_that_recovers_is_not_penalised(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _instant_sleep)
        calls = {"n": 0}

        async def fn(item):
            calls["n"] += 1
            if calls["n"] == 1:
                raise ls.HardcoverRateLimited("per-minute", retry_after=2)
            return True

        out = await ls._hc_rate_limited_loop([1], fn, time.monotonic() + 3600)
        assert out["linked"] == 1 and out["failed"] == 0


class TestCanonicalIdCollision:
    """book_links.hardcover_id is UNIQUE, so adopting Hardcover's canonical id
    blindly raised IntegrityError and aborted every cache_refresh run.

    Colliding does not imply the local books are duplicates: Hardcover keeps
    duplicate 'Untitled' placeholders for unannounced books and canonicalises one
    onto the other, while locally they are distinct series entries. Skipping is
    the safe behaviour; merging would destroy rows.
    """

    @pytest.mark.asyncio
    async def test_adopts_when_free(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            await db.execute("INSERT INTO books (id, title, created_at, updated_at) VALUES ('b1','B1','2026-01-01','2026-01-01')")
            await db.execute("INSERT INTO book_links (id, book_id, linked_at) VALUES ('l1','b1','2026-01-01')")
            await db.commit()
            assert await ls._adopt_canonical_hc_id(db, "b1", 999) is True
            await db.commit()
            row = await (await db.execute("SELECT hardcover_id FROM book_links WHERE book_id='b1'")).fetchone()
            assert row[0] == "999"

    @pytest.mark.asyncio
    async def test_skips_when_another_book_holds_it(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            await db.execute("INSERT INTO books (id, title, created_at, updated_at) VALUES ('b1','Empyrean 4','2026-01-01','2026-01-01')")
            await db.execute("INSERT INTO books (id, title, created_at, updated_at) VALUES ('b2','Empyrean 5','2026-01-01','2026-01-01')")
            await db.execute("INSERT INTO book_links (id, book_id, hardcover_id, linked_at) VALUES ('l1','b1','1061079','2026-01-01')")
            await db.execute("INSERT INTO book_links (id, book_id, hardcover_id, linked_at) VALUES ('l2','b2','1061078','2026-01-01')")
            await db.commit()

            # HC says 1061078 is canonically 1061079, which b1 already holds
            assert await ls._adopt_canonical_hc_id(db, "b2", 1061079) is False
            await db.commit()
            row = await (await db.execute("SELECT hardcover_id FROM book_links WHERE book_id='b2'")).fetchone()
            assert row[0] == "1061078", "b2 must keep its own link, not be merged into b1"

    @pytest.mark.asyncio
    async def test_reasserting_its_own_id_is_not_a_collision(self, db_path):
        from app.database import get_db
        async with get_db() as db:
            await db.execute("INSERT INTO books (id, title, created_at, updated_at) VALUES ('b1','B1','2026-01-01','2026-01-01')")
            await db.execute("INSERT INTO book_links (id, book_id, hardcover_id, linked_at) VALUES ('l1','b1','555','2026-01-01')")
            await db.commit()
            assert await ls._adopt_canonical_hc_id(db, "b1", 555) is True
