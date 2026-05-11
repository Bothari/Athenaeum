"""Hardcover search service for user-facing book search."""
import asyncio
import logging
import re

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


_SERIES_GQL = """
query GetSeriesBooks($id: Int!) {
  series_by_pk(id: $id) {
    id name
    book_series(
      order_by: [{position: asc}, {book: {users_count: desc}}]
      where: {
        book: {canonical_id: {_is_null: true}, is_partial_book: {_eq: false}}
        compilation: {_eq: false}
      }
    ) {
      position
      details
      book {
        id slug title users_count
        rating
        ratings_count
        release_date
        image { url }
        contributions(limit: 5) {
          author { id name }
        }
      }
    }
  }
}
"""


def _is_pure_position(details: str) -> bool:
    """True if details is purely numeric (e.g. '8', '4.5') — no text modifiers."""
    return bool(re.match(r'^[\d.]+$', details.strip()))


def _dedup_series_entries(entries: list[dict]) -> list[dict]:
    """
    Deduplicate raw book_series entries fetched without distinct_on.

    Two-pass strategy:
    1. Group by exact details string; keep the highest-users_count book per group.
    2. Group by numeric position; within each position, prefer pure-number details
       (e.g. '8') over split-book strings (e.g. '8 part 1', 'tome 1').
       If no pure-number entry exists at a position, keep the most popular.
    """
    # Pass 1: best book per exact details string; collect all IDs per details key
    by_details: dict[str, dict] = {}
    all_ids_by_details: dict[str, list[str]] = {}
    for e in entries:
        key = e.get("details") or ""
        bid = str((e.get("book") or {}).get("id") or "")
        if bid:
            all_ids_by_details.setdefault(key, []).append(bid)
        cur = by_details.get(key)
        if not cur or (e.get("users_count") or 0) > (cur.get("users_count") or 0):
            by_details[key] = e

    # Pass 2: group by numeric position, prefer pure-number details
    by_pos: dict[float, list[dict]] = {}
    for key, e in by_details.items():
        pos = e.get("position_num")
        if pos is None:
            continue
        e["_details_key"] = key
        by_pos.setdefault(pos, []).append(e)

    result = []
    for pos in sorted(by_pos):
        candidates = by_pos[pos]
        pure = [c for c in candidates if _is_pure_position(c.get("details") or "")]
        pool = pure if pure else candidates
        best = max(pool, key=lambda c: c.get("users_count") or 0)
        # Collect every HC book ID at this position that wasn't selected as winner
        winner_id = str((best.get("book") or {}).get("id") or "")
        alt_ids: list[str] = []
        for e in candidates:
            for bid in all_ids_by_details.get(e.get("_details_key") or "", []):
                if bid and bid != winner_id and bid not in alt_ids:
                    alt_ids.append(bid)
        best["_alt_ids"] = alt_ids
        result.append(best)

    return result


def _normalize_position(pos) -> str:
    if not pos:
        return ""
    pos = str(pos).strip()
    try:
        n = float(pos)
        return str(int(n)) if n == int(n) else str(n)
    except (ValueError, TypeError):
        return pos.lower()


async def get_hc_series_books(hc_series_id: str, api_key: str) -> list[dict]:
    """Fetch all books in a series using the official distinct_on dedup approach.

    Returns full normalised results (same shape as normalize_hit) with series_position set.
    Deduplication, merged-book filtering, and partial-edition filtering all happen server-side.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": _SERIES_GQL, "variables": {"id": int(hc_series_id)}},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("get_hc_series_books(%s) failed: %s", hc_series_id, e)
        return []

    series = (data.get("data") or {}).get("series_by_pk") or {}
    series_name = series.get("name") or ""

    # Collect raw entries, separating null-position (announced but unplaced) from positioned
    raw: list[dict] = []
    null_pos_raw: list[dict] = []
    for entry in (series.get("book_series") or []):
        book = entry.get("book") or {}
        if not book.get("title"):
            continue
        pos_raw = entry.get("position")
        try:
            pos_num = float(pos_raw) if pos_raw is not None else None
        except (ValueError, TypeError):
            pos_num = None
        item = {
            "entry": entry,
            "book": book,
            "details": entry.get("details") or "",
            "position_num": pos_num,
            "users_count": book.get("users_count") or 0,
        }
        if pos_num is None:
            null_pos_raw.append(item)
        else:
            raw.append(item)

    deduped = _dedup_series_entries(raw)

    def _normalise_item(item: dict, position: str) -> dict:
        book = item["book"]
        slug = book.get("slug") or ""
        book_id = str(book.get("id") or "")
        cover_url = (book.get("image") or {}).get("url") or ""
        rating_raw = book.get("rating") or 0
        release_date = book.get("release_date") or ""
        published_year = release_date[:4] if len(release_date) >= 4 else None
        authors = []
        seen_names: set = set()
        for c in (book.get("contributions") or []):
            a = c.get("author") or {}
            name = a.get("name") or ""
            if name and name not in seen_names:
                seen_names.add(name)
                authors.append({"name": name, "id": str(a.get("id") or "")})
        return {
            "title": book.get("title") or "",
            "subtitle": "",
            "author": authors[0]["name"] if authors else "",
            "author_id": authors[0]["id"] if authors else "",
            "authors": authors,
            "narrator": "",
            "description": "",
            "cover_url": cover_url,
            "isbn": "",
            "asin": "",
            "pages": None,
            "publisher": "",
            "release_date": release_date,
            "published_year": published_year,
            "language": "",
            "genres": [],
            "rating": round(float(rating_raw), 1) if rating_raw else None,
            "rating_count": book.get("ratings_count") or 0,
            "users_count": book.get("users_count") or 0,
            "series": [{"id": None, "hardcover_series_id": hc_series_id, "name": series_name, "position": position}],
            "is_compilation": False,
            "compilation": False,
            "metadata_source": "hardcover",
            "metadata_id": book_id,
            "slug": slug,
            "metadata_url": f"https://hardcover.app/books/{slug}" if slug else "",
            "hardcover_url": f"https://hardcover.app/books/{slug}" if slug else "",
            "book_id": None,
            "in_library": False,
            "library_formats": [],
            "existing_requests": [],
            "abs_links": [],
            "series_position": position,
            "alt_ids": item.get("_alt_ids") or [],
        }

    # Null-position books: dedup by book ID, keep highest users_count, show first
    null_pos_by_id: dict[str, dict] = {}
    for item in null_pos_raw:
        bid = str(item["book"].get("id") or "")
        if not bid:
            continue
        cur = null_pos_by_id.get(bid)
        if not cur or item["users_count"] > cur["users_count"]:
            null_pos_by_id[bid] = item
    null_results = [_normalise_item(item, "") for item in null_pos_by_id.values()]

    results = []
    for item in deduped:
        position = _normalize_position(item["entry"].get("details") or item["entry"].get("position") or "")
        if not position:
            continue
        results.append(_normalise_item(item, position))

    return null_results + results


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


_AUTHOR_GQL = """
query GetAuthorBooks($id: Int!) {
  authors_by_pk(id: $id) {
    id name
    contributions(
      where: {book: {canonical_id: {_is_null: true}}}
      order_by: [{book: {users_count: desc}}]
      limit: 50
    ) {
      book {
        id slug title users_count rating ratings_count
        image { url }
        contributions(limit: 5) { author { id name } }
        book_series(order_by: [{position: asc}], limit: 3) {
          position details
          series { id name }
        }
      }
    }
  }
}
"""


async def get_hc_author_books(hc_author_id: str, api_key: str) -> list[dict]:
    """Fetch books by HC author ID. Returns normalised results sorted by popularity."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": _AUTHOR_GQL, "variables": {"id": int(hc_author_id)}},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("get_hc_author_books(%s) failed: %s", hc_author_id, e)
        return []

    author_data = (data.get("data") or {}).get("authors_by_pk") or {}
    results = []

    for contrib in (author_data.get("contributions") or []):
        book = contrib.get("book") or {}
        title = book.get("title") or ""
        if not title:
            continue

        slug = book.get("slug") or ""
        book_id = str(book.get("id") or "")
        cover_url = (book.get("image") or {}).get("url") or ""
        rating_raw = book.get("rating") or 0

        authors = []
        seen_names: set = set()
        for c in (book.get("contributions") or []):
            a = c.get("author") or {}
            name = a.get("name") or ""
            if name and name not in seen_names:
                seen_names.add(name)
                authors.append({"name": name, "id": str(a.get("id") or "")})

        series_list = []
        seen_series: set = set()
        for bs in (book.get("book_series") or []):
            s = bs.get("series") or {}
            s_id = str(s.get("id") or "")
            s_name = s.get("name") or ""
            if not s_name and not s_id:
                continue
            if s_id in seen_series:
                continue
            seen_series.add(s_id or s_name)
            position = _normalize_position(bs.get("details") or bs.get("position") or "")
            series_list.append({
                "id": None,
                "hardcover_series_id": s_id,
                "name": s_name,
                "position": position,
            })

        result = {
            "title": title,
            "subtitle": "",
            "author": authors[0]["name"] if authors else "",
            "author_id": authors[0]["id"] if authors else "",
            "authors": authors,
            "narrator": "",
            "description": "",
            "cover_url": cover_url,
            "isbn": "",
            "asin": "",
            "pages": None,
            "publisher": "",
            "published_year": None,
            "language": "",
            "genres": [],
            "rating": round(float(rating_raw), 1) if rating_raw else None,
            "rating_count": book.get("ratings_count") or 0,
            "users_count": book.get("users_count") or 0,
            "series": series_list,
            "is_compilation": False,
            "metadata_source": "hardcover",
            "metadata_id": book_id,
            "slug": slug,
            "metadata_url": f"https://hardcover.app/books/{slug}" if slug else "",
            "hardcover_url": f"https://hardcover.app/books/{slug}" if slug else "",
            "book_id": None,
            "in_library": False,
            "library_formats": [],
            "existing_requests": [],
            "abs_links": [],
        }
        results.append(result)

    return results
