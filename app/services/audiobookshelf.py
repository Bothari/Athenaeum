import httpx
from rapidfuzz import fuzz


class AudiobookshelfService:
    def __init__(self, settings: dict):
        self.base_url = settings.get("url", "").rstrip("/")
        self.api_key = settings.get("api_key", "")
        library_ids = settings.get("library_id", [])
        if isinstance(library_ids, str):
            self.library_ids = [library_ids] if library_ids else []
        else:
            self.library_ids = list(library_ids or [])

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _item_url(self, item_id: str) -> str:
        return f"{self.base_url}/item/{item_id}"

    def _cover_url(self, item_id: str) -> str:
        return f"{self.base_url}/api/items/{item_id}/cover"

    def _normalize_item(self, item: dict) -> dict:
        item_id = item.get("id", "")
        media = item.get("media", {})
        meta = media.get("metadata", {})

        # Title
        title = meta.get("title", "")

        # Author — prefer structured list, fall back to flat string
        authors = meta.get("authors") or []
        author = authors[0]["name"] if authors else meta.get("authorName", "")

        # Series
        series_list = meta.get("series") or []
        series_name = series_list[0]["name"] if series_list else meta.get("seriesName", "")
        series_seq = str(series_list[0].get("sequence", "")) if series_list else ""

        # Narrator
        narrators = meta.get("narrators") or []
        narrator = narrators[0] if narrators else meta.get("narratorName", "")

        # Cover — only include URL if item actually has a cover
        cover_path = media.get("coverPath")
        cover_url = self._cover_url(item_id) if cover_path else ""

        # Formats — derived from whether item has audio tracks and/or an ebook file
        formats = []
        abs_url = self._item_url(item_id)
        tracks = media.get("tracks") or []
        num_tracks = media.get("numTracks") or 0
        ebook_file = media.get("ebookFile")

        if tracks or num_tracks:
            formats.append({
                "type": "audiobook",
                "narrator": narrator or "",
                "abs_id": item_id,
                "abs_url": abs_url,
            })
        if ebook_file:
            formats.append({"type": "ebook"})

        return {
            "abs_id": item_id,
            "abs_url": abs_url,
            "title": title,
            "author": author,
            "series": series_name,
            "series_sequence": series_seq,
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
        all_items = []
        async with httpx.AsyncClient(headers=self._headers(), timeout=60.0) as client:
            for lib_id in self.library_ids:
                resp = await client.get(
                    f"{self.base_url}/api/libraries/{lib_id}/items",
                    params={"limit": 0},
                )
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("results", []):
                    all_items.append(self._normalize_item(item))
        return all_items

    async def scan_library(self, library_id: str = None):
        lib_ids = [library_id] if library_id else self.library_ids
        async with httpx.AsyncClient(headers=self._headers(), timeout=15.0) as client:
            for lib_id in lib_ids:
                await client.post(f"{self.base_url}/api/libraries/{lib_id}/scan")
