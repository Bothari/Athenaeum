"""Prowlarr, qBittorrent, and SABnzbd client wrappers."""
import asyncio
import hashlib
import logging
import re
import struct

import httpx

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus", ".aac", ".wav"}


# ── Prowlarr ───────────────────────────────────────────────────────────────────

async def prowlarr_get_indexer_ids_for_tag(url: str, api_key: str, tag: str) -> list[int]:
    """Return IDs of enabled indexers whose tags include the given tag name (case-insensitive)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fetch all tags to build name→id map
        tags_resp = await client.get(f"{url}/api/v1/tag", headers={"X-Api-Key": api_key})
        tags_resp.raise_for_status()
        tag_id = None
        for t in tags_resp.json():
            if t.get("label", "").lower() == tag.lower():
                tag_id = t.get("id")
                break
        if tag_id is None:
            logger.warning("Prowlarr tag %r not found", tag)
            return []

        # Fetch all enabled indexers and filter by tag_id
        idx_resp = await client.get(f"{url}/api/v1/indexer", headers={"X-Api-Key": api_key})
        idx_resp.raise_for_status()
        return [
            i["id"] for i in idx_resp.json()
            if i.get("enable") and tag_id in (i.get("tags") or [])
        ]


PROWLARR_CATEGORIES = {
    "audiobook": [3030],
    "ebook": [7020],
}


async def prowlarr_search(settings: dict, query: str, book_type: str = "") -> list[dict]:
    """Search Prowlarr indexers. Filtered to configured tag if set."""
    url = (settings.get("url") or "").rstrip("/")
    api_key = settings.get("api_key") or ""
    if not url or not api_key:
        return []

    tag = (settings.get("tag") or "").strip()
    indexer_ids: list[int] = []
    if tag:
        try:
            indexer_ids = await prowlarr_get_indexer_ids_for_tag(url, api_key, tag)
            if not indexer_ids:
                logger.warning("Prowlarr tag %r matched no enabled indexers — returning empty results", tag)
                return []
            logger.info("Prowlarr tag %r → indexer IDs: %s", tag, indexer_ids)
        except Exception as e:
            logger.warning("Prowlarr tag lookup failed, searching all indexers: %s", e)

    # Build params as list of tuples so we can repeat indexerIds/categories for each value
    params: list[tuple] = [("query", query), ("type", "search"), ("limit", "50")]
    for iid in indexer_ids:
        params.append(("indexerIds", str(iid)))
    for cat in PROWLARR_CATEGORIES.get(book_type, []):
        params.append(("categories", str(cat)))

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{url}/api/v1/search",
            params=params,
            headers={"X-Api-Key": api_key},
        )
        resp.raise_for_status()
        return resp.json()


# ── qBittorrent ────────────────────────────────────────────────────────────────

class QBittorrentClient:
    def __init__(self, settings: dict):
        self._url = (settings.get("url") or "").rstrip("/")
        self._username = settings.get("username") or ""
        self._password = settings.get("password") or ""
        self._download_dir = settings.get("download_dir") or ""
        self._cookies: dict = {}

    async def _login(self, client: httpx.AsyncClient):
        resp = await client.post(
            f"{self._url}/api/v2/auth/login",
            data={"username": self._username, "password": self._password},
        )
        resp.raise_for_status()
        self._cookies = dict(resp.cookies)

    async def _request(self, client: httpx.AsyncClient, method: str, path: str, **kwargs):
        resp = await client.request(
            method, f"{self._url}{path}", cookies=self._cookies, **kwargs
        )
        if resp.status_code == 403:
            await self._login(client)
            resp = await client.request(
                method, f"{self._url}{path}", cookies=self._cookies, **kwargs
            )
        resp.raise_for_status()
        return resp

    async def add(self, download_url: str) -> str:
        """Add torrent/magnet. Returns the torrent hash."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._login(client)
            data = {"urls": download_url}
            if self._download_dir:
                data["savepath"] = self._download_dir
            data["category"] = "athenaeum"
            await self._request(client, "POST", "/api/v2/torrents/add", data=data)

            # Resolve hash
            if "magnet:" in download_url.lower():
                m = re.search(r"btih:([a-fA-F0-9]{40})", download_url, re.IGNORECASE)
                if not m:
                    raise ValueError(f"Cannot parse hash from magnet: {download_url}")
                torrent_hash = m.group(1).lower()
            else:
                # Download .torrent file and extract hash
                dl = await client.get(download_url)
                dl.raise_for_status()
                torrent_hash = _bencode_info_hash(dl.content)

            # Poll until the torrent appears
            for _ in range(20):
                await asyncio.sleep(0.5)
                r = await self._request(
                    client, "GET", f"/api/v2/torrents/info?hashes={torrent_hash}"
                )
                items = r.json()
                if items:
                    return torrent_hash
            raise TimeoutError(f"Torrent {torrent_hash} not seen after 10s")

    async def check(self, torrent_hash: str) -> dict:
        """Returns {'status': normalised_str, 'progress': 0-1, 'eta': int, 'speed': int, 'path': str}."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            await self._login(client)
            r = await self._request(
                client, "GET", f"/api/v2/torrents/info?hashes={torrent_hash}"
            )
            items = r.json()
        if not items:
            return {"status": "unknown"}
        t = items[0]
        state = t.get("state", "")
        path = t.get("content_path") or (
            (t.get("save_path") or "").rstrip("/") + "/" + (t.get("name") or "")
        )
        return {
            "status": _qbit_state(state),
            "progress": t.get("progress", 0),
            "eta": t.get("eta", -1),
            "speed": t.get("dlspeed", 0),
            "path": path,
            "size": t.get("size", 0),
        }


def _qbit_state(state: str) -> str:
    if state in ("uploading", "stalledUP", "forcedUP", "pausedUP", "queuedUP"):
        return "completed"
    if state in ("downloading", "stalledDL", "forcedDL", "metaDL"):
        return "downloading"
    if state in ("pausedDL", "queuedDL"):
        return "paused"
    if state in ("error", "missingFiles"):
        return "failed"
    return "downloading"


def _bencode_info_hash(data: bytes) -> str:
    """Extract the SHA1 hash of the 'info' dict from a bencoded .torrent file."""
    # Minimal bencode parser: find the 'info' key and hash the value bytes
    idx = data.find(b"4:info")
    if idx == -1:
        raise ValueError("No 'info' key found in torrent file")
    start = idx + 6  # skip "4:info"
    end = _bencode_end(data, start)
    return hashlib.sha1(data[start:end]).hexdigest()


def _bencode_end(data: bytes, pos: int) -> int:
    """Return the index just past the bencoded value starting at pos."""
    b = data[pos:pos + 1]
    if b == b"i":
        end = data.index(b"e", pos + 1)
        return end + 1
    if b == b"l":
        pos += 1
        while data[pos:pos + 1] != b"e":
            pos = _bencode_end(data, pos)
        return pos + 1
    if b == b"d":
        pos += 1
        while data[pos:pos + 1] != b"e":
            pos = _bencode_end(data, pos)  # key
            pos = _bencode_end(data, pos)  # value
        return pos + 1
    # string: N:...
    colon = data.index(b":", pos)
    n = int(data[pos:colon])
    return colon + 1 + n


# ── SABnzbd ────────────────────────────────────────────────────────────────────

class SABnzbdClient:
    def __init__(self, settings: dict):
        self._url = (settings.get("url") or "").rstrip("/")
        self._api_key = settings.get("api_key") or ""

    async def add(self, download_url: str) -> str:
        """Add NZB URL. Returns the SABnzbd job ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._url}/api",
                data={
                    "mode": "addurl",
                    "name": download_url,
                    "apikey": self._api_key,
                    "output": "json",
                    "cat": "athenaeum",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            nzo_ids = data.get("nzo_ids") or []
            if not nzo_ids:
                raise ValueError(f"SABnzbd did not return a job ID: {data}")
            return nzo_ids[0]

    async def check(self, job_id: str) -> dict:
        """Returns {'status': normalised_str, 'progress': 0-1, 'eta': str, 'speed': int, 'path': str}."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._url}/api",
                params={
                    "mode": "queue",
                    "apikey": self._api_key,
                    "output": "json",
                },
            )
            resp.raise_for_status()
            queue = resp.json().get("queue", {})

        for slot in queue.get("slots", []):
            if slot.get("nzo_id") == job_id:
                status = slot.get("status", "").lower()
                mb_total = float(slot.get("mb", 0) or 0)
                mb_left = float(slot.get("mbleft", 0) or 0)
                progress = (1 - mb_left / mb_total) if mb_total else 0
                return {
                    "status": "downloading",
                    "progress": progress,
                    "eta": slot.get("timeleft", ""),
                    "speed": 0,
                    "path": "",
                    "size": int(mb_total * 1024 * 1024),
                }

        # Not in queue — check history
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._url}/api",
                params={
                    "mode": "history",
                    "apikey": self._api_key,
                    "output": "json",
                },
            )
            resp.raise_for_status()
            history = resp.json().get("history", {})

        for slot in history.get("slots", []):
            if slot.get("nzo_id") == job_id:
                status = slot.get("status", "").lower()
                path = slot.get("storage") or ""
                if status == "completed":
                    return {"status": "completed", "progress": 1.0, "path": path, "eta": "", "speed": 0, "size": 0}
                if status == "failed":
                    return {"status": "failed", "progress": 0, "path": "", "eta": "", "speed": 0, "size": 0}

        return {"status": "unknown"}
