"""Prowlarr, qBittorrent, SABnzbd, and Deluge client wrappers."""
import asyncio
import base64
import hashlib
import logging
import os
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


# Words that are noise when detecting whether a result title has a meaningful
# prefix that changes book identity (e.g. "Call of the" in "Call of the Bone Ships").
_SCORE_STOP = frozenset({
    "a", "an", "the", "of", "by", "and", "in", "to", "for", "&", "or", "with",
    "from", "at", "on", "its",
})
_SCORE_FORMAT_NOISE = frozenset({
    "mp3", "m4b", "m4a", "flac", "epub", "mobi", "pdf", "azw3", "lit", "ogg",
    "opus", "aac", "wav", "cbz", "cbr", "audiobook", "ebook", "unabridged",
    "abridged", "eng", "english",
})


def _strip_subtitle(title: str) -> str:
    """Return the title with any subtitle after ': ' removed.

    Indexers almost never include the colon-separated subtitle in their release
    titles, so including it tends to produce zero results.  We keep everything
    before the first ': ' (e.g. 'You with the Sad Eyes: A Memoir' →
    'You with the Sad Eyes').  Single-word or no-space colons (e.g. URLs) are
    left untouched.
    """
    return re.split(r':\s+', title, maxsplit=1)[0].strip()


def _author_surname(author: str) -> str:
    """Return the surname from an author name, skipping initials and credentials.

    Handles formats like "Daniel J. Siegel, MD" → "Siegel",
    "S. A. Chakraborty" → "Chakraborty", "J. R. R. Tolkien" → "Tolkien".
    """
    _CREDENTIALS = frozenset({"md", "phd", "jr", "sr", "ii", "iii", "iv", "dds", "esq", "rn", "do", "mph"})
    tokens = re.sub(r"[^\w\s]", " ", author).split()
    for token in reversed(tokens):
        if len(token) > 2 and token.lower() not in _CREDENTIALS:
            return token
    return tokens[-1] if tokens else ""


def _score_result(result_title: str, original_title: str, author: str = "") -> int:
    """Score a Prowlarr result title against the book title+author (0–100).

    Uses token-set ratio so word order and extra tokens (e.g. '[MP3]', narrator
    name) don't hurt the score.  Author matching also checks the surname alone
    so pen-name initials (S. A. Chakraborty) match results filed under the
    author's full first name (Shannon Chakraborty).

    Extra penalty: if meaningful (non-noise) words appear in the result BEFORE
    the query's keywords, that strongly signals a different book (e.g. "Call of
    the Bone Ships" when searching for "The Bone Ships").  Score is capped low
    in that case so auto-search does not grab the wrong book.
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return 50
    clean_result = result_title.lower()
    full = original_title.lower()
    main = _strip_subtitle(original_title).lower()

    if main != full:
        # Title has a subtitle — it's the only thing distinguishing books in the
        # same series.  Subtitle must appear in the result or the score is capped.
        subtitle = full[len(main):].lstrip(': ').strip()
        subtitle_score = fuzz.partial_ratio(subtitle, clean_result) if subtitle else 100
        if subtitle_score < 60:
            t_score = int(subtitle_score * 0.5)
        else:
            t_score = int(fuzz.token_set_ratio(full, clean_result) * 0.6 + subtitle_score * 0.4)
    else:
        t_score = fuzz.token_set_ratio(full, clean_result)

    if author:
        a_full = fuzz.token_set_ratio(author.lower(), clean_result)
        surname = _author_surname(author).lower()
        a_surname = fuzz.partial_ratio(surname, clean_result) if surname else 0
        a_score = max(a_full, a_surname)
        score = int(t_score * 0.7 + a_score * 0.3)
    else:
        score = t_score

    # Prefix-word penalty: if meaningful words appear in the result *before* any
    # keyword from the query title, they almost certainly mean this is a different
    # book (e.g. "Call of the" preceding "Bone Ships").  Cap the score so
    # auto-search won't grab it automatically; the user can still pick it manually.
    score = _apply_prefix_penalty(score, clean_result, full, author)

    return score


def _apply_prefix_penalty(score: int, clean_result: str, full_title: str, author: str = "") -> int:
    """Cap score for two signals that a result is the wrong book:

    1. Missing keywords — query words that don't appear (even fuzzily) in the
       result (e.g. searching "Call of the Bone Ships" but result is "The Bone
       Ships").  If ≥33 % of meaningful query words are absent, cap the score.

    2. Prefix extra words — meaningful words in the result that appear *before*
       the query's first keyword (e.g. "Call of the" before "Bone Ships" when
       searching for "The Bone Ships").  Those words almost certainly mean it is
       a different book.
    """
    try:
        from rapidfuzz import fuzz as _fuzz
    except ImportError:
        return score

    noise = _SCORE_STOP | _SCORE_FORMAT_NOISE
    if author:
        noise = noise | set(re.sub(r'[^\w\s]', ' ', author.lower()).split())

    result_tokens = re.sub(r'[^\w\s]', ' ', clean_result).split()
    query_keywords = [
        t for t in re.sub(r'[^\w\s]', ' ', full_title).split()
        if t not in _SCORE_STOP and len(t) > 1
    ]
    if not query_keywords:
        return score

    # 1. Missing keyword penalty
    missing = [kw for kw in query_keywords if _fuzz.partial_ratio(kw, clean_result) < 80]
    if missing:
        missing_ratio = len(missing) / len(query_keywords)
        if missing_ratio >= 0.33:
            cap = 40 if missing_ratio >= 0.5 else 55
            score = min(score, cap)

    # 2. Prefix extra word penalty
    query_kw_set = set(query_keywords)
    first_match = next(
        (i for i, t in enumerate(result_tokens) if t in query_kw_set),
        len(result_tokens),
    )
    prefix_extra = [
        t for t in result_tokens[:first_match]
        if t not in noise and len(t) > 1
    ]
    if prefix_extra:
        cap = 55 if len(prefix_extra) == 1 else 40
        score = min(score, cap)

    return score


_FORMAT_RE = re.compile(
    r'\b(m4b|mp3|flac|opus|ogg|aac|wav|epub|pdf|mobi|azw3|lit|cbz|cbr)\b',
    re.IGNORECASE,
)


def _detect_format(title: str) -> str | None:
    """Return the first recognised format token found in a result title, or None."""
    m = _FORMAT_RE.search(title)
    return m.group(1).lower() if m else None


def build_prowlarr_query(title: str, author: str = "") -> str:
    """Build a Prowlarr search query, stripping subtitles indexers typically omit.

    Uses only the author's surname so pen-name initials (S. A. Chakraborty)
    don't prevent indexers from matching results filed under the full name.
    Hyphens are replaced with spaces — some indexers interpret a leading hyphen
    as a NOT operator (e.g. "No-Drama" → "No AND NOT Drama").
    """
    main = _strip_subtitle(title).replace("-", " ")
    surname = _author_surname(author)
    return f"{main} {surname}".strip() if surname else main


async def prowlarr_search(settings: dict, query: str, book_type: str = "", title: str = "", author: str = "", allowed_formats: list | None = None) -> list[dict]:
    """Search Prowlarr indexers. Filtered to configured tag if set.

    Pass `title` and `author` to enable relevance scoring — results are sorted
    by score descending so the best match surfaces first.  Pass `allowed_formats`
    to filter out results whose format tag is recognised but not in the list.
    """
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
        results = resp.json()

    if title and results:
        results = sorted(
            results,
            key=lambda r: _score_result(r.get("title", ""), title, author),
            reverse=True,
        )
    if allowed_formats:
        allowed_lower = {f.lower() for f in allowed_formats}
        results = [
            r for r in results
            if (fmt := _detect_format(r.get("title", ""))) is None or fmt in allowed_lower
        ]
    return results


# ── Downloader lookup helpers ──────────────────────────────────────────────────

def _make_client(dl: dict):
    """Instantiate the appropriate client class for a downloader entry."""
    t = dl.get("type", "")
    if t == "qbittorrent":
        return QBittorrentClient(dl)
    if t == "sabnzbd":
        return SABnzbdClient(dl)
    if t == "deluge":
        return DelugeClient(dl)
    return None


def get_torrent_client(settings: dict) -> tuple:
    """Return (client, client_ref) for the first enabled torrent downloader."""
    for dl in settings.get("downloaders", []):
        if dl.get("type") in ("qbittorrent", "deluge") and dl.get("enabled", True) and dl.get("url"):
            return _make_client(dl), dl.get("id", dl["type"])
    cfg = settings.get("qbittorrent", {})
    if isinstance(cfg, dict) and cfg.get("url"):
        return QBittorrentClient(cfg), "qbittorrent"
    return None, None


def get_usenet_client(settings: dict) -> tuple:
    """Return (SABnzbdClient, client_ref) for the first enabled usenet downloader."""
    for dl in settings.get("downloaders", []):
        if dl.get("type") == "sabnzbd" and dl.get("enabled", True) and dl.get("url"):
            return SABnzbdClient(dl), dl.get("id", "sabnzbd")
    cfg = settings.get("sabnzbd", {})
    if isinstance(cfg, dict) and cfg.get("url"):
        return SABnzbdClient(cfg), "sabnzbd"
    return None, None


def get_client_for_download(settings: dict, client_ref: str) -> tuple:
    """Return (client, type_str) for a download_client reference stored in the DB.

    Handles both new downloader IDs and legacy type-name strings.
    """
    for dl in settings.get("downloaders", []):
        if dl.get("id") == client_ref:
            return _make_client(dl), dl.get("type", "")
    for dl in settings.get("downloaders", []):
        if dl.get("type") == client_ref and dl.get("enabled", True):
            return _make_client(dl), dl.get("type", "")
    if client_ref == "qbittorrent":
        cfg = settings.get("qbittorrent", {})
        if isinstance(cfg, dict) and cfg.get("url"):
            return QBittorrentClient(cfg), "qbittorrent"
    elif client_ref == "sabnzbd":
        cfg = settings.get("sabnzbd", {})
        if isinstance(cfg, dict) and cfg.get("url"):
            return SABnzbdClient(cfg), "sabnzbd"
    return None, None


_TORRENT_CLIENT_TYPES = frozenset({"qbittorrent", "deluge"})


def is_torrent_client(client_ref: str, settings: dict) -> bool:
    """Return True if client_ref refers to a torrent download client.

    Accepts both downloader IDs (e.g. 'qbittorrent-1') and legacy type strings
    (e.g. 'qbittorrent').  Torrent clients need shutil.copy2 so the source file
    stays in place for continued seeding.
    """
    for dl in settings.get("downloaders", []):
        if dl.get("id") == client_ref or dl.get("type") == client_ref:
            return dl.get("type") in _TORRENT_CLIENT_TYPES
    return client_ref in _TORRENT_CLIENT_TYPES


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
                dl = await client.get(download_url, follow_redirects=True)
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
        self._category = settings.get("category") or "Default"
        self.remove_completed = bool(settings.get("remove_completed", False))

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
                    "cat": self._category,
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

    async def remove(self, job_id: str) -> None:
        """Remove a completed job from SABnzbd history, keeping the downloaded files."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._url}/api",
                params={
                    "mode": "history",
                    "name": "delete",
                    "value": job_id,
                    "del_files": "0",
                    "apikey": self._api_key,
                    "output": "json",
                },
            )
            resp.raise_for_status()


# ── Deluge ─────────────────────────────────────────────────────────────────────

class DelugeClient:
    """Client for the Deluge Web UI JSON-RPC API."""

    def __init__(self, settings: dict):
        self._url = (settings.get("url") or "").rstrip("/")
        self._password = settings.get("password") or ""
        self._download_dir = settings.get("download_dir") or ""
        self._cookies: dict = {}
        self._rpc_id = 0

    def _next_id(self) -> int:
        self._rpc_id += 1
        return self._rpc_id

    async def _call(self, client: httpx.AsyncClient, method: str, params: list):
        resp = await client.post(
            f"{self._url}/json",
            json={"method": method, "params": params, "id": self._next_id()},
            cookies=self._cookies,
            timeout=15.0,
        )
        resp.raise_for_status()
        self._cookies.update(dict(resp.cookies))
        data = resp.json()
        if data.get("error"):
            raise ValueError(f"Deluge error in {method}: {data['error'].get('message', data['error'])}")
        return data.get("result")

    async def _login(self, client: httpx.AsyncClient) -> None:
        ok = await self._call(client, "auth.login", [self._password])
        if not ok:
            raise ValueError("Deluge login failed — check password")
        connected = await self._call(client, "web.connected", [])
        if not connected:
            hosts = await self._call(client, "web.get_hosts", []) or []
            if not hosts:
                raise ValueError("Deluge: no daemon hosts configured in the web UI")
            await self._call(client, "web.connect", [hosts[0][0]])

    async def add(self, download_url: str) -> str:
        """Add a torrent/magnet. Returns the torrent hash."""
        options: dict = {}
        if self._download_dir:
            options["download_location"] = self._download_dir

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._login(client)
            if download_url.lower().startswith("magnet:"):
                torrent_hash = await self._call(client, "core.add_torrent_magnet", [download_url, options])
            else:
                dl = await client.get(download_url, follow_redirects=True)
                dl.raise_for_status()
                filename = (download_url.split("/")[-1].split("?")[0] or "download.torrent")
                if not filename.lower().endswith(".torrent"):
                    filename = "download.torrent"
                torrent_b64 = base64.b64encode(dl.content).decode()
                torrent_hash = await self._call(client, "core.add_torrent_file", [filename, torrent_b64, options])

        if not torrent_hash:
            raise ValueError("Deluge did not return a torrent hash")
        return torrent_hash.lower()

    async def check(self, torrent_hash: str) -> dict:
        """Returns {'status': normalised_str, 'progress': 0-1, 'eta': int, 'speed': int, 'path': str}."""
        fields = ["state", "progress", "save_path", "name", "eta", "download_payload_rate", "total_size"]
        async with httpx.AsyncClient(timeout=10.0) as client:
            await self._login(client)
            info = await self._call(client, "core.get_torrent_status", [torrent_hash, fields])

        if not info:
            return {"status": "unknown"}

        state = (info.get("state") or "").lower()
        progress = float(info.get("progress", 0)) / 100.0
        save_path = info.get("save_path") or ""
        name = info.get("name") or ""
        full_path = os.path.join(save_path, name) if save_path and name else save_path

        if state in ("seeding", "moving") or (state == "paused" and progress >= 1.0):
            return {"status": "completed", "progress": 1.0, "path": full_path,
                    "eta": 0, "speed": 0, "size": info.get("total_size", 0)}
        if state == "error":
            return {"status": "failed", "progress": 0, "path": "", "eta": 0, "speed": 0, "size": 0}

        return {"status": "downloading", "progress": progress, "path": "",
                "eta": info.get("eta", -1), "speed": info.get("download_payload_rate", 0),
                "size": info.get("total_size", 0)}
