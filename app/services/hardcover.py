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

# Hardcover's per-minute limiter is a token bucket, and it says so:
#   ratelimit-policy: "Free (JWT)";q=60;w=60;burst=5
# 60 requests per 60s, with a burst of 5. Ours is the same shape a little under
# it, so a search's page fan-out leaves at once and a long background job settles
# to roughly one request a second.
#
# A fixed delay was tried first and was wrong in both directions: a 3-page search
# paid ~3.6s of pure waiting, and it still collected per-minute 429s, because a
# delay cannot model a burst allowance — it can arrive exactly when the bucket is
# empty. Pacing must also be per request, not per item: one item in the linking
# loop is a _hc_book_search, which fans out to four requests.
# Equal capacity to theirs with a strictly slower refill means our request stream
# is always a subset of what they permit: after t seconds we can have sent at most
# 5 + 0.9167t where they allow 5 + 1.0t. So the bucket cannot trip their limiter,
# which a fixed delay could.
HC_BURST = 5.0
HC_PER_SECOND = 55.0 / 60.0   # 55/min sustained, against their 60

# A fresh process does not know what the ACCOUNT has already spent — another
# process, or a probe from elsewhere, draws on the same burst. So the bucket starts
# empty and earns its first token by waiting, which is the only state that is safe
# without knowledge. Measured, against an account whose burst was already at zero:
#
#   start full (5)  first fan-out fires 3 pages at once, two come back 429
#   start at 1      page 1 fires immediately and 429s — and since page 1 carries
#                   the hits, the search returned ZERO results
#   start at 0      every page waits for a real token; nothing is lost
#
# The cost is about a second on the first request a process makes. After that the
# header clamp keeps the count honest and the burst makes fan-outs free.
HC_INITIAL_TOKENS = 0.0

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

# The token bucket, shared by every caller in this process.
_hc_pace_lock: asyncio.Lock | None = None
_hc_tokens: float = HC_INITIAL_TOKENS
_hc_refilled: float | None = None   # monotonic reading of the last refill


async def _hc_pace() -> None:
    """Hold a request until the bucket has a token for it.

    The token is taken under the lock but the waiting happens outside it. Sleeping
    while holding the lock would serialise every caller — which is exactly what the
    fixed-delay version did, and why a page fan-out cost seconds. Taking the token
    can drive the count negative, and that is deliberate: it is what queues
    concurrent callers behind one another, each computing its own wait.

    The lock is built lazily so importing this module needs no running event loop.
    """
    global _hc_pace_lock, _hc_tokens, _hc_refilled
    if _hc_pace_lock is None:
        _hc_pace_lock = asyncio.Lock()

    async with _hc_pace_lock:
        now = time.monotonic()
        if _hc_refilled is None:
            _hc_refilled = now
        _hc_tokens = min(HC_BURST, _hc_tokens + (now - _hc_refilled) * HC_PER_SECOND)
        _hc_refilled = now

        wait = 0.0 if _hc_tokens >= 1.0 else (1.0 - _hc_tokens) / HC_PER_SECOND
        _hc_tokens -= 1.0

    if wait > 0:
        logger.debug("HC pacing: waiting %.2fs for a token", wait)
        await asyncio.sleep(wait)


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
    """Correct our local view from what Hardcover just reported.

    Our bucket starts full and only knows about this process, but the limit is on
    the account: another process, or a probe from somewhere else, drains the same
    burst. A fresh process therefore over-estimates what it has and trips the
    per-minute limiter on its first fan-out — which is exactly what happened the
    first time this was measured. Hardcover reports the true remaining burst on
    every response, so trust it over our own count.

    Only ever clamps downward. Raising the count from a header would be unsafe with
    requests in flight, since the header describes the moment that one was served.
    """
    global _hc_daily_remaining, _hc_tokens
    raw = resp.headers.get("x-ratelimit-daily-remaining")
    if raw is not None:
        try:
            _hc_daily_remaining = int(raw)
        except (TypeError, ValueError):
            pass

    raw_burst = resp.headers.get("x-ratelimit-remaining")
    if raw_burst is not None:
        try:
            _hc_tokens = min(_hc_tokens, float(raw_burst))
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
