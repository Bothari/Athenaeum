import asyncio

import httpx
from rapidfuzz import fuzz


class AudiobookshelfService:
    def __init__(self, settings: dict):
        self.public_url = settings.get("url", "").rstrip("/")
        internal = settings.get("internal_url", "").rstrip("/")
        self.base_url = internal or self.public_url
        self.api_key = settings.get("api_key", "")
        library_ids = settings.get("library_id", [])
        if isinstance(library_ids, str):
            self.library_ids = [library_ids] if library_ids else []
        else:
            self.library_ids = list(library_ids or [])

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _item_url(self, item_id: str) -> str:
        return f"{self.public_url}/item/{item_id}"

    def _cover_url(self, item_id: str) -> str:
        return f"{self.public_url}/api/items/{item_id}/cover"

    def _normalize_item(self, item: dict) -> dict:
        item_id = item.get("id", "")
        media = item.get("media", {})
        meta = media.get("metadata", {})

        # Title
        title = meta.get("title", "")

        # Authors — prefer structured list (has IDs), fall back to flat string
        authors_raw = meta.get("authors") or []
        if authors_raw:
            author_items = [
                {"name": a["name"], "abs_id": str(a.get("id") or "")}
                for a in authors_raw if a.get("name")
            ]
        else:
            author_items = [{"name": meta.get("authorName", ""), "abs_id": ""}]
        author = author_items[0]["name"] if author_items else ""

        # Series — may be a structured list or a flat string like "Name #1, Other #2"
        series_list = meta.get("series") or []
        series_items = []
        if series_list:
            for s in series_list:
                name = (s.get("name") or "").strip()
                seq = str(s.get("sequence") or "").strip()
                abs_series_id = str(s.get("id") or "").strip()
                if name:
                    series_items.append({"name": name, "sequence": seq, "abs_id": abs_series_id})
        elif meta.get("seriesName"):
            for part in meta["seriesName"].split(", "):
                part = part.strip()
                if not part:
                    continue
                import re as _re
                m = _re.match(r'^(.+?)\s*#([\d.]+)\s*$', part)
                if m:
                    series_items.append({"name": m.group(1).strip(), "sequence": m.group(2)})
                else:
                    series_items.append({"name": part, "sequence": ""})

        # Narrator
        narrators = meta.get("narrators") or []
        narrator = narrators[0] if narrators else meta.get("narratorName", "")

        # Cover — only include URL if item actually has a cover
        cover_path = media.get("coverPath")
        cover_url = self._cover_url(item_id) if cover_path else ""

        # Formats — derived from whether item has audio and/or an ebook file
        formats = []
        abs_url = self._item_url(item_id)
        audio_files = media.get("audioFiles") or []
        ebook_file = media.get("ebookFile")

        if audio_files:
            formats.append({
                "type": "audiobook",
                "narrator": narrator or "",
                "abs_id": item_id,
                "abs_url": abs_url,
            })
        # ebookFile is null in list-endpoint responses (minified); use ebookFormat as fallback
        ebook_format = media.get("ebookFormat") or ""
        if ebook_file or ebook_format:
            formats.append({"type": "ebook"})

        return {
            "abs_id": item_id,
            "abs_url": abs_url,
            "title": title,
            "author": author,
            "author_items": author_items,
            "series_items": series_items,
            "cover_url": cover_url,
            "narrator": narrator,
            "formats": formats,
        }

    async def test_connection(self) -> dict:
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            libs_resp = await client.get(f"{self.base_url}/api/libraries")
            libs_resp.raise_for_status()
            libs = libs_resp.json()
            return {
                "libraries": [
                    {"id": lib["id"], "name": lib["name"]}
                    for lib in libs.get("libraries", [])
                ],
            }

    async def find_item_by_path(
        self, dest_dir: str, filenames: set, book_type: str, title: str = "", abs_id: str = ""
    ) -> str | None:
        """Find the ABS item containing our organized files.

        Matches on <author_dir>/<title_dir>/<filename> — the last two directory
        components of dest_dir plus the filename — so the check is mount-point-agnostic.
        ABS and Athenaeum live in separate containers with different prefixes; the
        relative Author/Title/file.ext suffix is what they share.

        Fast-checks abs_id first (item may have been updated in-place), then falls
        through to a title search so a newly-created ABS item is also found.
        """
        import logging as _logging
        _log = _logging.getLogger(__name__)

        from pathlib import Path as _Path

        dest_parts = _Path(dest_dir).parts
        rel_base = "/".join(dest_parts[-2:]) if len(dest_parts) >= 2 else dest_parts[-1]
        suffixes = {f"{rel_base}/{fname}" for fname in filenames}

        _log.info("find_item_by_path: dest_dir=%s book_type=%s abs_id=%s", dest_dir, book_type, abs_id)
        _log.info("find_item_by_path: suffixes=%s", suffixes)

        def _matches(item: dict) -> bool:
            item_id = item.get("id", "?")
            lib_files = item.get("libraryFiles", [])
            _log.info("find_item_by_path: checking item %s — %d libraryFiles", item_id, len(lib_files))
            for lf in lib_files:
                lf_path = lf.get("metadata", {}).get("path", "").replace("\\", "/")
                matched_suffix = next((s for s in suffixes if lf_path.endswith(s)), None)
                if matched_suffix:
                    normalized = self._normalize_item(item)
                    fmt_types = [f["type"] for f in normalized["formats"]]
                    type_ok = book_type in fmt_types
                    _log.info("find_item_by_path: suffix match on %s — formats=%s type_ok=%s", lf_path, fmt_types, type_ok)
                    return type_ok
                else:
                    _log.info("find_item_by_path: no suffix match for lf_path=%s", lf_path)
            return False

        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            # Fast path: the book was already in ABS — check if our files are now in it.
            if abs_id:
                _log.info("find_item_by_path: fast path — fetching existing abs_id %s", abs_id)
                resp = await client.get(f"{self.base_url}/api/items/{abs_id}")
                _log.info("find_item_by_path: fast path response status=%s", resp.status_code)
                if resp.status_code == 200:
                    item = resp.json()
                    if _matches(item):
                        _log.info("find_item_by_path: fast path matched — returning %s", abs_id)
                        return self._normalize_item(item)["abs_id"]
                    _log.info("find_item_by_path: fast path no match — falling through to search")
                # Fall through — ABS may have created a new item for our organized files.

            # Search by title, fetch libraryFiles for each result, match on suffix.
            query = title or rel_base.rsplit("/", 1)[-1]
            _log.info("find_item_by_path: searching lib %s q=%r", self.library_ids, query)
            for lib_id in self.library_ids:
                resp = await client.get(
                    f"{self.base_url}/api/libraries/{lib_id}/search",
                    params={"q": query, "limit": 20},
                )
                _log.info("find_item_by_path: search status=%s results=%d", resp.status_code, len(resp.json().get("book", [])) if resp.status_code == 200 else -1)
                if resp.status_code != 200:
                    continue
                for entry in resp.json().get("book", []):
                    item = entry.get("libraryItem", entry)
                    if not item.get("libraryFiles") and item.get("id"):
                        _log.info("find_item_by_path: search result %s has no libraryFiles, fetching full item", item.get("id"))
                        full = await client.get(f"{self.base_url}/api/items/{item['id']}")
                        if full.status_code == 200:
                            item = full.json()
                    if _matches(item):
                        found_id = self._normalize_item(item)["abs_id"]
                        _log.info("find_item_by_path: search matched — returning %s", found_id)
                        return found_id
            _log.info("find_item_by_path: no match found")
        return None

    async def check_library(self, title: str, author: str) -> list[dict]:
        results = []
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            for lib_id in self.library_ids:
                resp = await client.get(
                    f"{self.base_url}/api/libraries/{lib_id}/search",
                    params={"q": title, "limit": 20},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for entry in data.get("book", []):
                    item = entry.get("libraryItem", entry)
                    normalized = self._normalize_item(item)
                    t_score = fuzz.partial_ratio(title.lower(), normalized["title"].lower())
                    a_score = (
                        fuzz.partial_ratio(author.lower(), normalized["author"].lower())
                        if author
                        else 100
                    )
                    if t_score >= 70 and a_score >= 60:
                        results.append(normalized)
        return results

    async def search_library(self, query: str) -> list[dict]:
        results = []
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            for lib_id in self.library_ids:
                resp = await client.get(
                    f"{self.base_url}/api/libraries/{lib_id}/search",
                    params={"q": query, "limit": 20},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                for entry in data.get("book", []):
                    item = entry.get("libraryItem", entry)
                    results.append(self._normalize_item(item))
        return results

    async def get_item_by_id(self, item_id: str) -> dict:
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/api/items/{item_id}")
            resp.raise_for_status()
            return self._normalize_item(resp.json())

    async def list_all_items(self) -> list[dict]:
        """Fetch all library items as fully-normalised dicts.

        The list endpoint returns minified items (no series IDs, no author IDs,
        no ebookFile). We fetch the full item for each ID concurrently — ABS is
        local so this is fast.
        """
        all_items = []
        sem = asyncio.Semaphore(20)

        async def fetch_full(client: httpx.AsyncClient, item_id: str):
            async with sem:
                resp = await client.get(f"{self.base_url}/api/items/{item_id}")
                resp.raise_for_status()
                return self._normalize_item(resp.json())

        async with httpx.AsyncClient(headers=self._headers(), timeout=30.0) as client:
            for lib_id in self.library_ids:
                resp = await client.get(
                    f"{self.base_url}/api/libraries/{lib_id}/items",
                    params={"limit": 0},
                )
                resp.raise_for_status()
                item_ids = [item["id"] for item in resp.json().get("results", [])]

                results = await asyncio.gather(
                    *[fetch_full(client, iid) for iid in item_ids],
                    return_exceptions=True,
                )
                for r in results:
                    if isinstance(r, Exception):
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to fetch ABS item: {r}")
                    else:
                        all_items.append(r)

        return all_items

    async def update_item_metadata(self, item_id: str, metadata: dict) -> bool:
        """Push metadata fields to an existing ABS item via PATCH /api/items/{id}/media."""
        try:
            async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
                resp = await client.patch(
                    f"{self.base_url}/api/items/{item_id}/media",
                    json={"metadata": metadata},
                )
                resp.raise_for_status()
                return True
        except Exception:
            return False

    async def scan_library(self, library_id: str = None):
        lib_ids = [library_id] if library_id else self.library_ids
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            for lib_id in lib_ids:
                await client.post(f"{self.base_url}/api/libraries/{lib_id}/scan")

    async def scan_folder(self, library_id: str, folder_path: str):
        """Scan a specific folder path within a library instead of the whole library."""
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            await client.post(
                f"{self.base_url}/api/libraries/{library_id}/scan",
                params={"folder": folder_path},
            )
