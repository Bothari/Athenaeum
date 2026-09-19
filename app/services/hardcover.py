"""Hardcover API client: one place that knows the service's rate limits.

Split out of library_sync so interactive search can share it. Search must not
depend on the sync engine, and both need identical 429 handling — a failure that
is invisible to one of them is how a rate limit reads as "no results".
"""

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)


# ── Hardcover rate limiting ───────────────────────────────────────────────────
#
# Hardcover publishes its budget on every response:
#   ratelimit-policy: "Free (JWT)";q=60;w=60;burst=5, "daily";q=5000;w=86400
# i.e. 60 requests per minute and 5000 per day, with the remaining allowance in
# x-ratelimit-remaining and x-ratelimit-daily-remaining.
#
# Two rules follow, and both exist because a retry storm once consumed the whole
# daily quota and took interactive search down with it until the window reset:
#
#  1. A 429 is a STOP, not a retry. The daily window resets hours later, so no
#     amount of in-run retrying can succeed, and a rejected request still counts
#     against the quota — retrying digs the hole deeper the longer it runs.
#  2. Background work yields before the quota is gone. Linking and metadata
#     refresh are never urgent; a user typing in the search box is. Background
#     stages stop once the daily allowance falls to HC_DAILY_RESERVE, leaving
#     that much for interactive search until the window resets.

HC_API_URL = "https://api.hardcover.app/v1/graphql"

# Requests held back from background work so interactive search keeps working
# until the daily window resets.
HC_DAILY_RESERVE = 500

# Minimum spacing between individual Hardcover REQUESTS, enforced globally in
# hc_post. The per-minute allowance is 60, so 1.0s sits exactly on the limit and
# 1.2s (50/min) leaves room for an interactive search sharing the budget.
#
# This has to be per-request, not per-item: one "item" in the linking loop is a
# _hc_book_search, which fans out to four requests (three pages plus a
# title+author query). Pacing per item ran at roughly 200 requests/min against a
# 60/min ceiling, so it sat permanently in per-minute throttling — burning quota
# on rejected requests while making almost no progress.
HC_MIN_REQUEST_INTERVAL = 1.2

# A 429 whose retry-after is under this is the per-minute window, which is worth
# waiting out. Anything longer is the daily quota, which resets hours later and
# must end the cycle instead.
HC_SHORT_WAIT_MAX = 90.0

# How many times one item may be re-attempted after a short throttle before it is
# abandoned. Each attempt costs that item's whole request fan-out, so this is a
# quota guard, not just a liveness guard.
HC_MAX_THROTTLE_RETRIES = 3

# Last daily allowance Hardcover reported, shared across every call site in this
# module. None means nothing has been observed yet this process.
_hc_daily_remaining: int | None = None

# Serialises request pacing across every concurrent caller in this process.
_hc_pace_lock: asyncio.Lock | None = None
_hc_last_request: float = 0.0


async def _hc_pace() -> None:
    """Block until HC_MIN_REQUEST_INTERVAL has passed since the previous request.

    The lock is built lazily so importing this module needs no running event loop.
    """
    global _hc_pace_lock, _hc_last_request
    if _hc_pace_lock is None:
        _hc_pace_lock = asyncio.Lock()
    async with _hc_pace_lock:
        wait = _hc_last_request + HC_MIN_REQUEST_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _hc_last_request = time.monotonic()


class HardcoverRateLimited(Exception):
    """Hardcover refused the request, or background work has spent its share of
    the daily quota. Always aborts the current cache_refresh cycle."""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


async def _hc_wait_or_abort(exc: "HardcoverRateLimited", deadline: float) -> None:
    """Sleep out a brief per-minute throttle, or re-raise to end the cycle.

    The two Hardcover limits need opposite responses: the per-minute one clears in
    seconds and is worth waiting for, while the daily one resets hours later, so
    retrying it only burns more of a quota that is already gone.
    """
    wait = exc.retry_after
    if wait <= 0 or wait > HC_SHORT_WAIT_MAX or time.monotonic() + wait >= deadline:
        raise exc
    logger.info("HC throttled for %.0fs (per-minute window), waiting it out", wait)
    await asyncio.sleep(wait)


def hc_daily_remaining() -> int | None:
    """Daily allowance as of the last response, for callers that want to report it."""
    return _hc_daily_remaining


def _hc_note_headers(resp: httpx.Response) -> None:
    global _hc_daily_remaining
    raw = resp.headers.get("x-ratelimit-daily-remaining")
    if raw is None:
        return
    try:
        _hc_daily_remaining = int(raw)
    except (TypeError, ValueError):
        pass


def _hc_retry_after(resp: httpx.Response) -> float:
    try:
        return float(resp.headers.get("retry-after") or 0.0)
    except (TypeError, ValueError):
        return 0.0


async def hc_post(
    gql: str,
    variables: dict,
    api_key: str,
    *,
    background: bool = True,
    timeout: float = 10.0,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """POST a GraphQL query to Hardcover, honouring the published rate limits.

    Raises HardcoverRateLimited on a 429, and — when background is True — before
    sending at all if the daily allowance has fallen to the reserve. Callers in
    background stages must let that exception propagate so the cycle ends;
    swallowing it reinstates the retry storm this exists to prevent.
    """
    if background and _hc_daily_remaining is not None and _hc_daily_remaining <= HC_DAILY_RESERVE:
        raise HardcoverRateLimited(
            f"daily quota down to {_hc_daily_remaining}, holding the last "
            f"{HC_DAILY_RESERVE} for interactive search"
        )

    async def _send(c: httpx.AsyncClient) -> dict:
        await _hc_pace()
        resp = await c.post(
            HC_API_URL,
            json={"query": gql, "variables": variables},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        _hc_note_headers(resp)
        if resp.status_code == 429:
            raise HardcoverRateLimited(
                f"Hardcover rate limit reached ({resp.headers.get('ratelimit', 'no policy header')})",
                retry_after=_hc_retry_after(resp),
            )
        resp.raise_for_status()
        return resp.json()

    if client is not None:
        return await _send(client)
    async with httpx.AsyncClient(timeout=timeout) as c:
        return await _send(c)
