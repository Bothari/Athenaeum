"""Hardcover search service for user-facing book search."""
import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_SEARCH_GQL = (
    'query Search($q: String!, $page: Int!) {'
    '  search(query: $q, query_type: "Book", per_page: 25, page: $page) { results }'
    '}'
)


# ── Normalisation helpers ──────────────────────────────────────────────────────

def _cover_url(doc: dict) -> str:
    # Typesense book docs use "image" (dict with url/width/height)
    img = doc.get("image") or doc.get("cached_image") or {}
    if isinstance(img, dict):
        return img.get("url") or ""
    if isinstance(img, str):
        return img
    return ""


def _all_authors(doc: dict) -> list[tuple[str, str]]:
    """Return list of (name, hardcover_author_id) for all contributors."""
    seen: set = set()
    result = []
    for c in (doc.get("contributions") or doc.get("cached_contributors") or []):
        if not isinstance(c, dict):
            continue
        author = c.get("author") or {}
        name = c.get("author_name") or author.get("name") or ""
        author_id = str(author.get("id") or "")
        if name and name not in seen:
            seen.add(name)
            result.append((name, author_id))
    return result


def _primary_author(doc: dict) -> tuple[str, str]:
    """Return (name, hardcover_author_id) for the primary contributor."""
    authors = _all_authors(doc)
    return authors[0] if authors else ("", "")


def _series_list(doc: dict, context_hc_series_id: str = "") -> list[dict]:
    """Extract series from Typesense book document."""
    series = []

    # featured_series carries HC series ID + position
    featured = doc.get("featured_series") or {}
    if featured:
        s = featured.get("series") or {}
        s_id = str(s.get("id") or "")
        name = s.get("name") or ""
        position = featured.get("position") or ""
        if name or s_id:
            series.append({
                "id": None,
                "hardcover_series_id": s_id,
                "name": name,
                "position": str(position) if position else "",
            })

    # series_names: name-only strings for additional series
    names_seen = {s["name"] for s in series}
    for name in (doc.get("series_names") or []):
        if name and name not in names_seen:
            series.append({
                "id": None,
                "hardcover_series_id": "",
                "name": name,
                "position": "",
            })
            names_seen.add(name)

    if context_hc_series_id:
        series.sort(key=lambda s: 0 if s["hardcover_series_id"] == context_hc_series_id else 1)

    return series


def normalize_hit(doc: dict, context_hc_series_id: str = "") -> dict:
    """Normalise a Typesense book document into the search result shape."""
    all_authors = _all_authors(doc)
    author, author_id = all_authors[0] if all_authors else ("", "")
    slug = doc.get("slug") or ""
    raw_rating = doc.get("rating") or 0
    return {
        "title": doc.get("title") or "",
        "subtitle": doc.get("subtitle") or "",
        "author": author,
        "author_id": author_id,
        "authors": [{"name": n, "id": aid} for n, aid in all_authors],
        "narrator": "",
        "description": "",
        "cover_url": _cover_url(doc),
        "isbn": "",
        "asin": "",
        "pages": doc.get("pages") or None,
        "publisher": "",
        "published_year": str(doc.get("release_year") or "") or None,
        "language": "",
        "genres": [],
        "rating": round(float(raw_rating), 1) if raw_rating else None,
        "rating_count": doc.get("ratings_count") or 0,
        "users_count": doc.get("users_count") or 0,
        "series": _series_list(doc, context_hc_series_id),
        "is_compilation": False,
        "compilation_details": "",
        "metadata_source": "hardcover",
        "metadata_id": str(doc.get("id") or ""),
        "slug": slug,
        "metadata_url": f"https://hardcover.app/books/{slug}" if slug else "",
        "hardcover_url": f"https://hardcover.app/books/{slug}" if slug else "",
        # Annotation fields — populated by the route handler after a DB lookup
        "book_id": None,
        "in_library": False,
        "library_formats": [],
        "existing_requests": [],
        "abs_links": [],
    }


# ── Search ─────────────────────────────────────────────────────────────────────

async def _fetch_page(client: httpx.AsyncClient, query: str, page: int, api_key: str) -> list:
    resp = await client.post(
        "https://api.hardcover.app/v1/graphql",
        json={"query": _SEARCH_GQL, "variables": {"q": query, "page": page}},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    resp.raise_for_status()
    return resp.json()["data"]["search"]["results"].get("hits", [])


async def search_books(
    query: str,
    api_key: str,
    pages: int = 3,
    context_hc_series_id: str = "",
) -> list[dict]:
    """Search HC by free-text query. Returns normalised results sorted by popularity."""
    if not query.strip() or not api_key:
        return []

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(
            *[_fetch_page(client, query, p, api_key) for p in range(1, pages + 1)],
            return_exceptions=True,
        )

    seen: set = set()
    docs: list = []
    for r in results:
        if not isinstance(r, list):
            continue
        for h in r:
            doc = h.get("document", {})
            doc_id = doc.get("id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                docs.append(doc)

    docs.sort(key=lambda d: d.get("users_count") or 0, reverse=True)
    return [normalize_hit(d, context_hc_series_id) for d in docs]


async def advanced_search_books(
    title: str = "",
    author: str = "",
    series: str = "",
    api_key: str = "",
    context_hc_series_id: str = "",
) -> list[dict]:
    """Advanced search — builds query from individual fields."""
    parts = [p.strip() for p in [title, author, series] if p.strip()]
    if not parts:
        return []
    query = " ".join(parts)
    return await search_books(query, api_key, pages=3, context_hc_series_id=context_hc_series_id)
