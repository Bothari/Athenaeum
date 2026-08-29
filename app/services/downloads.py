"""Single place a download row is created.

Before this module the same INSERT was hand-written in three routes/services
against two near-identical tables, which is how the two schemas drifted apart
(separate poller loops, separate organizer entry points, and two different
words for "done"). Mirrors the `_create_request()` convention: never inline.
"""

import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NoClientConfigured(Exception):
    """No download client is configured for the requested protocol."""


def select_client(settings: dict, protocol: str) -> tuple:
    """Resolve (client, client_name) for a protocol.

    Raises NoClientConfigured so callers can translate it into whatever their
    layer needs — an HTTP 400 in a route, a logged failure in a background task.
    """
    from .download_clients import get_torrent_client, get_usenet_client

    if protocol == "torrent":
        client, name = get_torrent_client(settings)
        if not client:
            raise NoClientConfigured("No torrent downloader configured")
    elif protocol == "usenet":
        client, name = get_usenet_client(settings)
        if not client:
            raise NoClientConfigured("No usenet downloader configured")
    else:
        raise NoClientConfigured(f"Unknown protocol: {protocol}")
    return client, name


async def create_download(
    db,
    *,
    release: dict,
    download_client: str,
    download_id: str,
    request_id: str = None,
    series_id: str = None,
    type: str = None,
) -> str:
    """Record a grabbed release. Returns the new download id.

    Exactly one of request_id / series_id identifies what the grab was for; that
    choice sets `kind`. Does not commit — the caller owns the transaction, since
    every call site also has request status or event rows to write atomically.

    `release` is the raw Prowlarr result dict, so both its camelCase keys
    (infoUrl) and the flat ones the manual-grab body uses (info_url) are read.
    """
    if (request_id is None) == (series_id is None):
        raise ValueError("pass exactly one of request_id or series_id")

    kind = "request" if request_id else "series_pack"
    dl_id = str(uuid.uuid4())
    now = _now()

    await db.execute(
        """INSERT OR IGNORE INTO downloads
           (id, kind, request_id, series_id, type, title, indexer, guid,
            info_url, protocol, size, download_client, download_id,
            status, grabbed_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'snatched', ?, ?)""",
        (
            dl_id, kind, request_id, series_id, type,
            release.get("title"),
            release.get("indexer"),
            release.get("guid"),
            release.get("infoUrl") or release.get("info_url"),
            release.get("protocol"),
            release.get("size"),
            download_client, download_id, now, now,
        ),
    )
    return dl_id
