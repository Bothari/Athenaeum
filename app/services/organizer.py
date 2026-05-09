"""File organisation pipeline: move → metadata.json → ABS scan → poll."""
import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".flac", ".ogg", ".opus", ".aac", ".wav"}
EBOOK_EXTENSIONS = {".epub", ".mobi", ".azw", ".azw3", ".pdf"}

_HC_BOOK_GQL = (
    "query GetBook($id: Int!) {"
    "  books(where: {id: {_eq: $id}}) {"
    "    id slug title subtitle description release_year"
    "    rating ratings_count users_count"
    "    cached_image cached_contributors cached_tags"
    "    contributions(order_by: {id: asc}) {"
    "      contribution author { id name }"
    "    }"
    "    book_series {"
    "      position details featured compilation"
    "      series { id name }"
    "    }"
    "    editions(order_by: {users_count: desc}, limit: 5) {"
    "      isbn_10 isbn_13 asin pages audio_seconds release_year"
    "      language { language }"
    "      publisher { name }"
    "    }"
    "  }"
    "}"
)


def _sanitise_path_component(s: str) -> str:
    """Strip characters illegal on common filesystems."""
    s = re.sub(r'[<>:"/\\|?*]', "", s)
    s = s.strip(". ")
    return s or "Unknown"


def _natural_sort_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.stem.lower())
    return tuple(int(p) if p.isdigit() else p for p in parts)


def _collect_audio_files(directory: Path) -> list[Path]:
    files = [
        f for f in directory.rglob('*')
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return sorted(files, key=_natural_sort_key)


def _is_multifile_audio(path: Path) -> bool:
    if not path.is_dir():
        return False
    return len(_collect_audio_files(path)) >= 2


def _build_dest_dir(settings: dict, book_type: str, author: str, title: str) -> Path:
    output_dir = settings.get("general", {}).get("output_dir") or "/output"
    separate = settings.get("general", {}).get("separate_type_dirs", True)
    if book_type == "audiobook":
        prefix = settings.get("general", {}).get("audiobook_prefix") or ""
    else:
        prefix = settings.get("general", {}).get("ebook_prefix") or ""

    parts = [output_dir]
    if separate and prefix:
        parts.append(_sanitise_path_component(prefix))
    parts.append(_sanitise_path_component(author))
    parts.append(_sanitise_path_component(title))
    return Path(*parts)


def _dedup_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


# ── HC metadata cache ──────────────────────────────────────────────────────────

async def _fetch_hc_book_metadata(hc_book_id: str, api_key: str) -> dict:
    """Fetch HC book metadata and return a flat dict for metadata.json population."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": _HC_BOOK_GQL, "variables": {"id": int(hc_book_id)}},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("HC book fetch failed for id=%s: %s", hc_book_id, e)
        return {}

    books = (data.get("data") or {}).get("books") or []
    if not books:
        return {}
    book = books[0]

    # Subtitle
    subtitle = book.get("subtitle") or ""

    # Description
    description = book.get("description") or ""

    # Genres from cached_tags
    tags = book.get("cached_tags") or {}
    genres = tags.get("Genre") or []

    # Publisher / ISBN / ASIN / language from editions
    publisher = ""
    isbn = ""
    asin = ""
    language = ""
    for ed in (book.get("editions") or []):
        if not publisher:
            publisher = (ed.get("publisher") or {}).get("name") or ""
        if not isbn:
            isbn = ed.get("isbn_13") or ed.get("isbn_10") or ""
        if not asin:
            asin = ed.get("asin") or ""
        if not language:
            language = (ed.get("language") or {}).get("language") or ""

    # Published year
    published_year = str(book.get("release_year") or "")

    return {
        "subtitle": subtitle,
        "description": description,
        "genres": genres,
        "publisher": publisher,
        "isbn": isbn,
        "asin": asin,
        "language": language,
        "published_year": published_year,
    }


async def _get_hc_metadata(db, book_id: str, api_key: str) -> dict:
    """Get HC metadata for a book, using/populating the metadata_cache lazily."""
    # Get hardcover_id
    link_row = await (
        await db.execute(
            "SELECT hardcover_id FROM book_links WHERE book_id = ?", (book_id,)
        )
    ).fetchone()
    hc_id = (link_row["hardcover_id"] if link_row else None) or ""
    if not hc_id or not api_key:
        return {}

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()

    cache_row = await (
        await db.execute(
            "SELECT results_json FROM metadata_cache WHERE query = ? AND source = ? AND expires_at > ?",
            (hc_id, "hardcover_book", now_iso),
        )
    ).fetchone()

    if cache_row:
        return json.loads(cache_row["results_json"])

    # Cache miss — fetch live
    meta = await _fetch_hc_book_metadata(hc_id, api_key)
    if meta:
        expires_iso = (now_dt + timedelta(days=14)).isoformat()
        await db.execute(
            """INSERT INTO metadata_cache (id, query, source, results_json, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(query, source) DO UPDATE SET
                 results_json = excluded.results_json,
                 created_at = excluded.created_at,
                 expires_at = excluded.expires_at""",
            (str(uuid.uuid4()), hc_id, "hardcover_book",
             json.dumps(meta), now_iso, expires_iso),
        )
        await db.commit()

    return meta


async def _build_abs_metadata(db, book_id: str, narrator: str, api_key: str) -> dict:
    """Build the metadata dict for PATCH /api/items/{id}/media from DB + HC."""
    book_row = await (await db.execute("SELECT title FROM books WHERE id = ?", (book_id,))).fetchone()
    if not book_row:
        return {}

    author_rows = await (await db.execute(
        "SELECT a.name FROM authors a JOIN book_authors ba ON ba.author_id = a.id WHERE ba.book_id = ? ORDER BY ba.author_position",
        (book_id,),
    )).fetchall()
    series_rows = await (await db.execute(
        "SELECT s.name, bs.position FROM series s JOIN book_series bs ON bs.series_id = s.id WHERE bs.book_id = ?",
        (book_id,),
    )).fetchall()

    hc_meta = await _get_hc_metadata(db, book_id, api_key)

    meta: dict = {"title": book_row["title"]}
    if author_rows:
        meta["authorName"] = ", ".join(r["name"] for r in author_rows)
    if narrator:
        narrators = [n.strip() for n in narrator.split(",") if n.strip()]
        if narrators:
            meta["narratorName"] = ", ".join(narrators)
    if series_rows:
        meta["series"] = [
            {"name": r["name"], "sequence": (r["position"] or "").strip()}
            for r in series_rows
        ]
    if hc_meta.get("subtitle"):
        meta["subtitle"] = hc_meta["subtitle"]
    if hc_meta.get("description"):
        meta["description"] = hc_meta["description"]
    if hc_meta.get("genres"):
        meta["genres"] = hc_meta["genres"]
    if hc_meta.get("published_year"):
        meta["publishedYear"] = str(hc_meta["published_year"])
    if hc_meta.get("publisher"):
        meta["publisher"] = hc_meta["publisher"]
    if hc_meta.get("isbn"):
        meta["isbn"] = hc_meta["isbn"]
    if hc_meta.get("asin"):
        meta["asin"] = hc_meta["asin"]
    if hc_meta.get("language"):
        meta["language"] = hc_meta["language"]
    return meta


# ── metadata.opf ──────────────────────────────────────────────────────────────

async def write_metadata_opf(target_dir: Path, db, book_id: str, narrator: str, api_key: str):
    """Write a metadata.opf file to target_dir. ABS reads this on library scan."""
    book_row = await (
        await db.execute("SELECT title FROM books WHERE id = ?", (book_id,))
    ).fetchone()
    if not book_row:
        return
    title = book_row["title"]

    author_rows = await (
        await db.execute(
            """SELECT a.name FROM authors a
               JOIN book_authors ba ON ba.author_id = a.id
               WHERE ba.book_id = ?
               ORDER BY ba.author_position""",
            (book_id,),
        )
    ).fetchall()
    authors = [r["name"] for r in author_rows]

    series_rows = await (
        await db.execute(
            """SELECT s.name, bs.position FROM series s
               JOIN book_series bs ON bs.series_id = s.id
               WHERE bs.book_id = ?""",
            (book_id,),
        )
    ).fetchall()

    narrators = [n.strip() for n in (narrator or "").split(",") if n.strip()]

    hc_meta = await _get_hc_metadata(db, book_id, api_key)

    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0">',
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">',
        f'    <dc:title>{esc(title)}</dc:title>',
    ]
    for author in authors:
        lines.append(f'    <dc:creator opf:role="aut">{esc(author)}</dc:creator>')
    for n in narrators:
        lines.append(f'    <dc:creator opf:role="nrt">{esc(n)}</dc:creator>')
    if hc_meta.get("description"):
        lines.append(f'    <dc:description>{esc(hc_meta["description"])}</dc:description>')
    if hc_meta.get("publisher"):
        lines.append(f'    <dc:publisher>{esc(hc_meta["publisher"])}</dc:publisher>')
    if hc_meta.get("published_year"):
        lines.append(f'    <dc:date>{esc(str(hc_meta["published_year"]))}</dc:date>')
    if hc_meta.get("language"):
        lines.append(f'    <dc:language>{esc(hc_meta["language"])}</dc:language>')
    if hc_meta.get("isbn"):
        lines.append(f'    <dc:identifier opf:scheme="ISBN">{esc(hc_meta["isbn"])}</dc:identifier>')
    if hc_meta.get("asin"):
        lines.append(f'    <dc:identifier opf:scheme="ASIN">{esc(hc_meta["asin"])}</dc:identifier>')
    if series_rows:
        first = series_rows[0]
        pos = (first["position"] or "").strip()
        lines.append(f'    <meta name="calibre:series" content="{esc(first["name"])}"/>')
        if pos:
            lines.append(f'    <meta name="calibre:series_index" content="{esc(pos)}"/>')
    lines += [
        '  </metadata>',
        '</package>',
    ]

    dest = target_dir / "metadata.opf"
    dest.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote metadata.opf to %s", dest)


# ── M4B merge ──────────────────────────────────────────────────────────────────

async def _merge_to_m4b(source_dir: Path, output_path: Path, title: str, author: str):
    """Merge all audio files in source_dir into a single M4B at output_path."""
    files = _collect_audio_files(source_dir)
    if not files:
        raise ValueError(f"No audio files found in {source_dir}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        filelist = tmp_path / "filelist.txt"
        ffmeta = tmp_path / "chapters.ffmetadata"

        # Collect durations via ffprobe
        durations = []
        for f in files:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(f),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            try:
                durations.append(float(stdout.strip()))
            except (ValueError, TypeError):
                durations.append(0.0)

        # Determine codec: copy if all inputs are m4a/m4b, else re-encode
        exts = {f.suffix.lower() for f in files}
        use_copy = exts <= {".m4a", ".m4b"}
        if not use_copy:
            total_dur = sum(durations)
            avg_bitrate = 128  # kbps default

        # Write filelist
        lines = [f"file '{str(f)}'\n" for f in files]
        filelist.write_text("".join(lines))

        # Write ffmetadata chapter file
        chapters = [";FFMETADATA1\n"]
        cursor_ms = 0
        for f, dur in zip(files, durations):
            dur_ms = int(dur * 1000)
            chapters.append("[CHAPTER]\n")
            chapters.append("TIMEBASE=1/1000\n")
            chapters.append(f"START={cursor_ms}\n")
            chapters.append(f"END={cursor_ms + dur_ms}\n")
            chapters.append(f"title={f.stem}\n")
            cursor_ms += dur_ms
        ffmeta.write_text("".join(chapters))

        # Build ffmpeg command
        codec_args = ["-c", "copy"] if use_copy else ["-c:a", "aac", "-b:a", f"{avg_bitrate}k"]
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(filelist),
            "-i", str(ffmeta),
            "-map_metadata", "1",
            "-map", "0:a",
            *codec_args,
            "-metadata", f"title={title}",
            "-metadata", f"artist={author}",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode(errors="replace"))

    logger.info("Merged %d files to %s", len(files), output_path)


# ── Main organize pipeline ─────────────────────────────────────────────────────

async def auto_organize(request_id: str):
    """Detached background task: move → metadata.json → ABS scan → poll."""
    from ..database import get_db
    from ..settings import get_settings
    from .audiobookshelf import AudiobookshelfService

    def _now():
        return datetime.now(timezone.utc).isoformat()

    try:
        settings = await get_settings()
        api_key = settings.get("hardcover", {}).get("api_key") or ""
        abs_settings = settings.get("audiobookshelf", {})

        async with get_db() as db:
            req_row = await (
                await db.execute(
                    """SELECT r.id, r.book_id, r.type, r.narrator, r.status,
                              b.title,
                              (SELECT a.name FROM authors a
                               JOIN book_authors ba ON ba.author_id = a.id
                               WHERE ba.book_id = r.book_id
                               ORDER BY ba.author_position LIMIT 1) as author
                       FROM requests r JOIN books b ON b.id = r.book_id
                       WHERE r.id = ?""",
                    (request_id,),
                )
            ).fetchone()
            if not req_row:
                logger.error("auto_organize: request %s not found", request_id)
                return

            dl_row = await (
                await db.execute(
                    "SELECT download_path, download_client FROM downloads WHERE request_id = ? ORDER BY grabbed_at DESC LIMIT 1",
                    (request_id,),
                )
            ).fetchone()

        book_id = req_row["book_id"]
        book_type = req_row["type"]
        title = req_row["title"]
        author = req_row["author"] or "Unknown"
        narrator = req_row["narrator"] or ""
        path_str = dl_row["download_path"] if dl_row else None
        download_client = dl_row["download_client"] if dl_row else None

        if not path_str:
            logger.error("auto_organize: no download_path for request %s", request_id)
            async with get_db() as db:
                await db.execute(
                    "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                    (_now(), request_id),
                )
                await db.commit()
            return

        src = Path(path_str)

        # ── Merge step ──────────────────────────────────────────────────────────
        if (
            book_type == "audiobook"
            and settings.get("general", {}).get("merge_multifile_audiobooks")
            and _is_multifile_audio(src)
        ):
            file_count = len(_collect_audio_files(src))
            merge_id = str(uuid.uuid4())
            now = _now()
            async with get_db() as db:
                await db.execute(
                    """INSERT OR IGNORE INTO merge_jobs
                       (id, request_id, source_path, file_count, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (merge_id, request_id, str(src), file_count, now, now),
                )
                await db.execute(
                    "UPDATE requests SET status='merging', updated_at=? WHERE id=?",
                    (now, request_id),
                )
                await db.commit()

            tmp_output = Path(tempfile.mkdtemp()) / f"{_sanitise_path_component(title)}.m4b"
            try:
                await _merge_to_m4b(src, tmp_output, title, author)
            except Exception as e:
                logger.error("M4B merge failed for request %s: %s", request_id, e)
                async with get_db() as db:
                    await db.execute(
                        "UPDATE merge_jobs SET merge_error=?, updated_at=? WHERE request_id=?",
                        (str(e), _now(), request_id),
                    )
                    await db.execute(
                        "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                        (_now(), request_id),
                    )
                    await db.commit()
                return

            async with get_db() as db:
                await db.execute(
                    "UPDATE merge_jobs SET merged_path=?, updated_at=? WHERE request_id=?",
                    (str(tmp_output), _now(), request_id),
                )
                await db.commit()
            src = tmp_output

        # ── Organizing ─────────────────────────────────────────────────────────
        async with get_db() as db:
            await db.execute(
                "UPDATE requests SET status='organizing', updated_at=? WHERE id=?",
                (_now(), request_id),
            )
            await db.commit()

        dest_dir = _build_dest_dir(settings, book_type, author, title)
        dest_dir.mkdir(parents=True, exist_ok=True)

        organized_filenames: set[str] = set()
        safe_title = _sanitise_path_component(title)
        safe_author = _sanitise_path_component(author)

        if src.is_dir():
            COVER_NAMES = {"cover.jpg", "cover.jpeg", "cover.png"}
            type_exts = AUDIO_EXTENSIONS if book_type == "audiobook" else EBOOK_EXTENSIONS
            media_files = sorted(
                [f for f in src.rglob('*') if f.is_file() and f.suffix.lower() in type_exts],
                key=_natural_sort_key,
            )
            # For ebooks, keep only the best format when multiple are present
            if book_type == "ebook" and len(media_files) > 1:
                EBOOK_PREF = [".epub", ".mobi", ".azw3", ".azw", ".pdf"]
                for preferred_ext in EBOOK_PREF:
                    preferred = [f for f in media_files if f.suffix.lower() == preferred_ext]
                    if preferred:
                        media_files = preferred[:1]
                        break
            cover_file = next(
                (f for f in src.rglob('*') if f.is_file() and f.name.lower() in COVER_NAMES),
                None,
            )
            for i, item in enumerate(media_files):
                if len(media_files) == 1:
                    stem = f"{safe_title} - {safe_author}"
                else:
                    stem = f"{safe_title} - {safe_author} - {i + 1:02d}"
                fname = f"{stem}{item.suffix.lower()}"
                organized_filenames.add(fname)
                dst = dest_dir / fname
                if dst.exists() or dst == item:
                    continue
                if download_client == "qbittorrent":
                    await asyncio.to_thread(shutil.copy2, str(item), str(dst))
                else:
                    await asyncio.to_thread(shutil.move, str(item), str(dst))
            if cover_file:
                dst = dest_dir / cover_file.name.lower()
                if dst != cover_file:
                    if download_client == "qbittorrent":
                        await asyncio.to_thread(shutil.copy2, str(cover_file), str(dst))
                    else:
                        await asyncio.to_thread(shutil.move, str(cover_file), str(dst))
        elif src.is_file():
            ext = src.suffix
            fname = f"{safe_title} - {safe_author}{ext}"
            organized_filenames.add(fname)
            dest_file = dest_dir / fname
            if dest_file.exists() or dest_file == src:
                pass  # already in place
            elif download_client == "qbittorrent":
                await asyncio.to_thread(shutil.copy2, str(src), str(dest_file))
            else:
                await asyncio.to_thread(shutil.move, str(src), str(dest_file))
        else:
            logger.error("auto_organize: source path does not exist: %s", src)
            async with get_db() as db:
                await db.execute(
                    "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                    (_now(), request_id),
                )
                await db.commit()
            return

        # Update merge_jobs.organized_path if present
        async with get_db() as db:
            await db.execute(
                "UPDATE merge_jobs SET organized_path=?, updated_at=? WHERE request_id=?",
                (str(dest_dir), _now(), request_id),
            )
            await db.commit()

        # ── Write metadata.json ─────────────────────────────────────────────────
        try:
            async with get_db() as db:
                await write_metadata_opf(dest_dir, db, book_id, narrator, api_key)
        except Exception as e:
            logger.warning("metadata.json write failed for request %s: %s", request_id, e)

        # ── ABS scan + poll ─────────────────────────────────────────────────────
        if not abs_settings.get("url"):
            logger.info("No ABS URL configured, leaving request %s as organizing", request_id)
            async with get_db() as db:
                await db.execute(
                    "UPDATE requests SET status='completed', updated_at=? WHERE id=?",
                    (_now(), request_id),
                )
                await db.commit()
            return

        abs_svc = AudiobookshelfService(abs_settings)
        library_ids = abs_settings.get("library_id") or []
        if isinstance(library_ids, str):
            library_ids = [lid.strip() for lid in library_ids.split(",") if lid.strip()]

        for lib_id in library_ids:
            try:
                await abs_svc.scan_library(lib_id)
            except Exception as e:
                logger.warning("ABS scan_library(%s) failed: %s", lib_id, e)

        await asyncio.sleep(5)

        # Poll for match by filename — 12 attempts × 5s = 60s.
        # Check the already-linked abs_id first (file may have been added to an existing item),
        # then fall back to a library search.
        matched_abs_id = None
        async with get_db() as db:
            link_row = await (
                await db.execute("SELECT abs_id FROM book_links WHERE book_id = ?", (book_id,))
            ).fetchone()
        existing_abs_id = link_row["abs_id"] if link_row else None

        for attempt in range(12):
            try:
                if existing_abs_id:
                    matched_abs_id = await abs_svc.find_item_by_filename(
                        organized_filenames, book_type, abs_id=existing_abs_id
                    )
                if not matched_abs_id:
                    matched_abs_id = await abs_svc.find_item_by_filename(
                        organized_filenames, book_type, title=title
                    )
            except Exception as e:
                logger.warning("ABS find_item_by_filename attempt %d failed: %s", attempt + 1, e)
            if matched_abs_id:
                break
            await asyncio.sleep(5)

        # Push authoritative metadata to ABS now that we have the item ID.
        # This overwrites whatever ABS parsed from audio tags with our HC/DB data.
        if matched_abs_id:
            try:
                async with get_db() as db:
                    meta_payload = await _build_abs_metadata(db, book_id, narrator, api_key)
                ok = await abs_svc.update_item_metadata(matched_abs_id, meta_payload)
                if not ok:
                    logger.warning("ABS metadata update failed for item %s", matched_abs_id)
            except Exception as e:
                logger.warning("ABS metadata update error for %s: %s", matched_abs_id, e)

        now = _now()
        async with get_db() as db:
            if matched_abs_id:
                await db.execute(
                    "UPDATE requests SET status='in_library', updated_at=? WHERE id=?",
                    (now, request_id),
                )
                # Upsert book_links with abs_id
                await db.execute(
                    """INSERT INTO book_links (id, book_id, abs_id, linked_at)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(book_id) DO UPDATE SET abs_id=excluded.abs_id, linked_at=excluded.linked_at""",
                    (str(uuid.uuid4()), book_id, matched_abs_id, now),
                )
                # Upsert book_formats with abs_id/abs_url so the detail page can link to ABS
                abs_url = f"{abs_svc.public_url}/item/{matched_abs_id}"
                await db.execute(
                    """INSERT INTO book_formats
                           (id, book_id, type, narrator, abs_id, abs_url, fulfilled_by_request_id, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(book_id, type) DO UPDATE SET
                           abs_id   = excluded.abs_id,
                           abs_url  = excluded.abs_url,
                           updated_at = excluded.updated_at""",
                    (str(uuid.uuid4()), book_id, book_type, narrator,
                     matched_abs_id, abs_url, request_id, now, now),
                )
                # Delete merge_jobs row once in library
                await db.execute("DELETE FROM merge_jobs WHERE request_id=?", (request_id,))
                logger.info("Request %s organised and in library (abs_id=%s)", request_id, matched_abs_id)
            else:
                await db.execute(
                    "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                    (now, request_id),
                )
                logger.warning(
                    "Request %s: ABS poll exhausted without finding item — marked failed",
                    request_id,
                )
            await db.commit()

        if matched_abs_id:
            import asyncio as _asyncio
            from .notifications import notify as _notify
            _asyncio.create_task(_notify("in_library", {
                "title": title,
                "author": author,
                "type": book_type,
            }))

    except Exception as e:
        logger.error("auto_organize crashed for request %s: %s", request_id, e, exc_info=True)
        try:
            from ..database import get_db
            async with get_db() as db:
                await db.execute(
                    "UPDATE requests SET status='failed', updated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), request_id),
                )
                await db.commit()
        except Exception:
            pass


# ── Series pack organizer ──────────────────────────────────────────────────────

def _clean_pack_filename(stem: str) -> str:
    """Strip pack-filename noise for fuzzy title matching."""
    # Remove leading position prefix: "01 - ", "1. ", "#1 - "
    stem = re.sub(r'^[\d#]+[.\-\s]+', '', stem)
    # Remove trailing author suffix: " - Glen Cook"
    stem = re.sub(r'\s+-\s+[^-]+$', '', stem)
    # Remove underscore-based subtitle: "_ The Fourth Chronicles of t"
    stem = re.sub(r'_\s+.*', '', stem)
    # Remove bracketed/parenthesised tokens: [EPUB], (Retail), [ENG], etc.
    stem = re.sub(r'\s*[\[\(][^\]\)]*[\]\)]', '', stem)
    # Remove known format keywords
    stem = re.sub(r'\b(epub|mobi|azw3?|pdf|retail|scan)\b', '', stem, flags=re.IGNORECASE)
    return stem.strip()


def _read_epub_title(path: Path) -> str | None:
    """Extract dc:title from an epub file. Returns None on any error."""
    try:
        with zipfile.ZipFile(str(path)) as zf:
            container = zf.read("META-INF/container.xml").decode("utf-8", errors="ignore")
            m = re.search(r'full-path="([^"]+\.opf)"', container)
            if not m:
                return None
            opf = zf.read(m.group(1)).decode("utf-8", errors="ignore")
            t = re.search(r'<dc:title[^>]*>([^<]+)</dc:title>', opf, re.IGNORECASE)
            return t.group(1).strip() if t else None
    except Exception:
        return None


async def compute_series_pack_mappings(series_dl_id: str):
    """Scan downloaded files, propose book mappings, set status=awaiting_review."""
    from ..database import get_db

    def _now():
        return datetime.now(timezone.utc).isoformat()

    try:
        async with get_db() as db:
            sdl_row = await (
                await db.execute("SELECT * FROM series_downloads WHERE id = ?", (series_dl_id,))
            ).fetchone()
        if not sdl_row:
            logger.error("compute_series_pack_mappings: record %s not found", series_dl_id)
            return

        series_id = sdl_row["series_id"]
        pack_type = sdl_row["type"] or "ebook"
        path_str = sdl_row["download_path"]

        if not path_str:
            logger.error("compute_series_pack_mappings: no download_path for %s", series_dl_id)
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                    (_now(), series_dl_id),
                )
                await db.commit()
            return

        async with get_db() as db:
            book_rows = await (
                await db.execute(
                    """SELECT b.id, b.title, bs.position
                       FROM books b
                       JOIN book_series bs ON bs.book_id = b.id
                       WHERE bs.series_id = ?""",
                    (series_id,),
                )
            ).fetchall()

        src = Path(path_str)
        type_exts = EBOOK_EXTENSIONS if pack_type == "ebook" else AUDIO_EXTENSIONS
        if src.is_dir():
            media_files = sorted(
                [f for f in src.rglob('*') if f.is_file() and f.suffix.lower() in type_exts],
                key=_natural_sort_key,
            )
        elif src.is_file() and src.suffix.lower() in type_exts:
            media_files = [src]
        else:
            logger.error("compute_series_pack_mappings: invalid source %s", src)
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                    (_now(), series_dl_id),
                )
                await db.commit()
            return

        from rapidfuzz import fuzz

        file_mappings = []
        for media_file in media_files:
            stem = _clean_pack_filename(media_file.stem)

            best_score = 0
            best_book = None
            for book in book_rows:
                score = fuzz.token_sort_ratio(stem.lower(), book["title"].lower())
                if score > best_score:
                    best_score = score
                    best_book = book

            if best_score < 75 and media_file.suffix.lower() == ".epub":
                epub_title = _read_epub_title(media_file)
                if epub_title:
                    for book in book_rows:
                        score = fuzz.token_sort_ratio(epub_title.lower(), book["title"].lower())
                        if score > best_score:
                            best_score = score
                            best_book = book

            if best_score < 75 or best_book is None:
                file_mappings.append({
                    "filepath": str(media_file),
                    "filename": media_file.name,
                    "book_id": None,
                    "book_title": None,
                    "best_guess_book_id": best_book["id"] if best_book else None,
                    "best_guess_book_title": best_book["title"] if best_book else None,
                    "score": best_score,
                    "action": "no_match",
                })
                continue

            book_id = best_book["id"]
            async with get_db() as db:
                fmt_row = await (
                    await db.execute(
                        "SELECT id FROM book_formats WHERE book_id = ? AND type = ?",
                        (book_id, pack_type),
                    )
                ).fetchone()

            action = "skip_in_library" if fmt_row else "place"
            file_mappings.append({
                "filepath": str(media_file),
                "filename": media_file.name,
                "book_id": book_id,
                "book_title": best_book["title"],
                "score": best_score,
                "action": action,
            })

        # Build series_books list with in-library status (one batch query)
        if book_rows:
            placeholders = ','.join('?' for _ in book_rows)
            async with get_db() as db:
                lib_rows = await (
                    await db.execute(
                        f"SELECT book_id FROM book_formats WHERE book_id IN ({placeholders}) AND type = ?",
                        [b["id"] for b in book_rows] + [pack_type],
                    )
                ).fetchall()
            in_library_set = {r["book_id"] for r in lib_rows}
        else:
            in_library_set = set()

        series_books = [
            {
                "id": b["id"],
                "title": b["title"],
                "position": b["position"] or "",
                "in_library": b["id"] in in_library_set,
            }
            for b in book_rows
        ]

        mappings_data = {"series_books": series_books, "file_mappings": file_mappings}

        async with get_db() as db:
            await db.execute(
                "UPDATE series_downloads SET status='awaiting_review', proposed_mappings=?, updated_at=? WHERE id=?",
                (json.dumps(mappings_data), _now(), series_dl_id),
            )
            await db.commit()

        place_count = sum(1 for m in file_mappings if m["action"] == "place")
        logger.info(
            "compute_series_pack_mappings: %s — %d files, %d to place, %d series books",
            series_dl_id, len(file_mappings), place_count, len(series_books),
        )

    except Exception as e:
        logger.error("compute_series_pack_mappings crashed for %s: %s", series_dl_id, e, exc_info=True)
        try:
            from ..database import get_db
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), series_dl_id),
                )
                await db.commit()
        except Exception:
            pass


async def auto_organize_series_pack(series_dl_id: str):
    """Place confirmed series pack files, scan ABS, update DB."""
    from ..database import get_db
    from ..settings import get_settings
    from .audiobookshelf import AudiobookshelfService

    def _now():
        return datetime.now(timezone.utc).isoformat()

    try:
        settings = await get_settings()
        api_key = settings.get("hardcover", {}).get("api_key") or ""
        abs_settings = settings.get("audiobookshelf", {})

        async with get_db() as db:
            sdl_row = await (
                await db.execute("SELECT * FROM series_downloads WHERE id = ?", (series_dl_id,))
            ).fetchone()
        if not sdl_row:
            logger.error("auto_organize_series_pack: record %s not found", series_dl_id)
            return

        pack_type = sdl_row["type"] or "ebook"
        download_client = sdl_row["download_client"]
        mappings_raw = sdl_row["proposed_mappings"]

        if not mappings_raw:
            logger.error("auto_organize_series_pack: no proposed_mappings for %s", series_dl_id)
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                    (_now(), series_dl_id),
                )
                await db.commit()
            return

        # Only process entries the user confirmed (action == 'place')
        to_place = [m for m in json.loads(mappings_raw) if m.get("action") == "place"]

        if not to_place:
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='completed', updated_at=? WHERE id=?",
                    (_now(), series_dl_id),
                )
                await db.commit()
            return

        # (dest_dir, book_id, req_row, filenames_set, narrator)
        placed: list[tuple] = []

        for mapping in to_place:
            filepath = mapping["filepath"]
            book_id = mapping["book_id"]
            media_file = Path(filepath)

            if not media_file.exists():
                logger.warning("auto_organize_series_pack: file not found: %s", filepath)
                continue

            async with get_db() as db:
                book_row = await (
                    await db.execute(
                        """SELECT b.title,
                                  (SELECT a.name FROM authors a
                                   JOIN book_authors ba ON ba.author_id = a.id
                                   WHERE ba.book_id = b.id
                                   ORDER BY ba.author_position LIMIT 1) as author
                           FROM books b WHERE b.id = ?""",
                        (book_id,),
                    )
                ).fetchone()
                if not book_row:
                    logger.warning("auto_organize_series_pack: book %s not found", book_id)
                    continue

                # Re-check in case something changed since compute step
                fmt_row = await (
                    await db.execute(
                        "SELECT id FROM book_formats WHERE book_id = ? AND type = ?",
                        (book_id, pack_type),
                    )
                ).fetchone()
                if fmt_row:
                    logger.info("auto_organize_series_pack: %s already in library, skipping", book_row["title"])
                    continue

                req_row = await (
                    await db.execute(
                        """SELECT id, narrator FROM requests
                           WHERE book_id = ? AND type = ?
                           AND status NOT IN ('failed', 'completed', 'rejected', 'in_library')""",
                        (book_id, pack_type),
                    )
                ).fetchone()

            title = book_row["title"]
            author = book_row["author"] or "Unknown"
            narrator = req_row["narrator"] if req_row else ""

            dest_dir = _build_dest_dir(settings, pack_type, author, title)
            dest_dir.mkdir(parents=True, exist_ok=True)

            fname = f"{_sanitise_path_component(title)} - {_sanitise_path_component(author)}{media_file.suffix.lower()}"
            dest_file = dest_dir / fname

            if not dest_file.exists():
                if download_client == "qbittorrent":
                    await asyncio.to_thread(shutil.copy2, str(media_file), str(dest_file))
                else:
                    await asyncio.to_thread(shutil.move, str(media_file), str(dest_file))

            try:
                async with get_db() as db:
                    await write_metadata_opf(dest_dir, db, book_id, narrator or "", api_key)
            except Exception as e:
                logger.warning("auto_organize_series_pack: metadata.opf for %s: %s", title, e)

            placed.append((dest_dir, book_id, req_row, {fname}, narrator or ""))
            logger.info("auto_organize_series_pack: placed %s → %s", media_file.name, dest_file)

        if not placed:
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='completed', updated_at=? WHERE id=?",
                    (_now(), series_dl_id),
                )
                await db.commit()
            return

        # Single ABS scan then per-book poll
        if abs_settings.get("url"):
            abs_svc = AudiobookshelfService(abs_settings)
            library_ids = abs_settings.get("library_id") or []
            if isinstance(library_ids, str):
                library_ids = [lid.strip() for lid in library_ids.split(",") if lid.strip()]

            for lib_id in library_ids:
                try:
                    await abs_svc.scan_library(lib_id)
                except Exception as e:
                    logger.warning("auto_organize_series_pack: scan_library(%s) failed: %s", lib_id, e)

            await asyncio.sleep(5)

            for (dest_dir, book_id, req_row, filenames, narrator) in placed:
                async with get_db() as db:
                    link_row = await (
                        await db.execute("SELECT abs_id FROM book_links WHERE book_id = ?", (book_id,))
                    ).fetchone()
                existing_abs_id = link_row["abs_id"] if link_row else None

                matched_abs_id = None
                for attempt in range(8):
                    try:
                        if existing_abs_id:
                            matched_abs_id = await abs_svc.find_item_by_filename(
                                filenames, pack_type, abs_id=existing_abs_id
                            )
                        if not matched_abs_id:
                            title_hint = next(iter(filenames), "").rsplit(" - ", 1)[0]
                            matched_abs_id = await abs_svc.find_item_by_filename(
                                filenames, pack_type, title=title_hint
                            )
                    except Exception as e:
                        logger.warning("auto_organize_series_pack: ABS poll %d: %s", attempt + 1, e)
                    if matched_abs_id:
                        break
                    await asyncio.sleep(5)

                now = _now()
                fulfilled_req_id = req_row["id"] if req_row else None

                async with get_db() as db:
                    if matched_abs_id:
                        abs_url = f"{abs_svc.public_url}/item/{matched_abs_id}"
                        await db.execute(
                            """INSERT INTO book_links (id, book_id, abs_id, linked_at)
                               VALUES (?, ?, ?, ?)
                               ON CONFLICT(book_id) DO UPDATE SET
                                   abs_id=excluded.abs_id, linked_at=excluded.linked_at""",
                            (str(uuid.uuid4()), book_id, matched_abs_id, now),
                        )
                        await db.execute(
                            """INSERT INTO book_formats
                                   (id, book_id, type, narrator, abs_id, abs_url,
                                    fulfilled_by_request_id, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ON CONFLICT(book_id, type) DO UPDATE SET
                                   abs_id=excluded.abs_id, abs_url=excluded.abs_url,
                                   fulfilled_by_request_id=COALESCE(excluded.fulfilled_by_request_id, fulfilled_by_request_id),
                                   updated_at=excluded.updated_at""",
                            (str(uuid.uuid4()), book_id, pack_type, narrator,
                             matched_abs_id, abs_url, fulfilled_req_id, now, now),
                        )
                    else:
                        await db.execute(
                            """INSERT INTO book_formats
                                   (id, book_id, type, narrator, abs_id, abs_url,
                                    fulfilled_by_request_id, created_at, updated_at)
                               VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                               ON CONFLICT(book_id, type) DO NOTHING""",
                            (str(uuid.uuid4()), book_id, pack_type, narrator, fulfilled_req_id, now, now),
                        )
                    if req_row:
                        await db.execute(
                            "UPDATE requests SET status='in_library', updated_at=? WHERE id=?",
                            (now, req_row["id"]),
                        )
                    await db.commit()

                if matched_abs_id:
                    try:
                        async with get_db() as db:
                            meta_payload = await _build_abs_metadata(db, book_id, narrator, api_key)
                        await abs_svc.update_item_metadata(matched_abs_id, meta_payload)
                    except Exception as e:
                        logger.warning("auto_organize_series_pack: ABS metadata error for %s: %s", matched_abs_id, e)
        else:
            now = _now()
            async with get_db() as db:
                for (dest_dir, book_id, req_row, filenames, narrator) in placed:
                    fulfilled_req_id = req_row["id"] if req_row else None
                    await db.execute(
                        """INSERT INTO book_formats
                               (id, book_id, type, narrator, abs_id, abs_url,
                                fulfilled_by_request_id, created_at, updated_at)
                           VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                           ON CONFLICT(book_id, type) DO NOTHING""",
                        (str(uuid.uuid4()), book_id, pack_type, narrator, fulfilled_req_id, now, now),
                    )
                    if req_row:
                        await db.execute(
                            "UPDATE requests SET status='in_library', updated_at=? WHERE id=?",
                            (now, req_row["id"]),
                        )
                await db.commit()

        async with get_db() as db:
            await db.execute(
                "UPDATE series_downloads SET status='completed', updated_at=? WHERE id=?",
                (_now(), series_dl_id),
            )
            await db.commit()

        logger.info("auto_organize_series_pack: completed, placed %d files", len(placed))

    except Exception as e:
        logger.error("auto_organize_series_pack crashed for %s: %s", series_dl_id, e, exc_info=True)
        try:
            from ..database import get_db
            async with get_db() as db:
                await db.execute(
                    "UPDATE series_downloads SET status='failed', updated_at=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), series_dl_id),
                )
                await db.commit()
        except Exception:
            pass
