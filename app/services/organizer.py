"""File organisation pipeline: move → metadata.json → ABS scan → poll."""
import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import uuid
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
        f for f in directory.iterdir()
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
        parts = []
        for r in series_rows:
            pos = (r["position"] or "").strip()
            parts.append(f"{r['name']} #{pos}" if pos else r["name"])
        meta["seriesName"] = ", ".join(parts)
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


# ── metadata.json ──────────────────────────────────────────────────────────────

async def write_metadata_json(target_dir: Path, db, book_id: str, narrator: str, api_key: str):
    """Write ABS-compatible metadata.json to target_dir."""
    # Core DB fields
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
    series_strs = []
    for r in series_rows:
        pos = (r["position"] or "").strip()
        series_strs.append(f"{r['name']} #{pos}" if pos else r["name"])

    narrators = [n.strip() for n in (narrator or "").split(",") if n.strip()]

    # HC enrichment (lazy cache)
    hc_meta = await _get_hc_metadata(db, book_id, api_key)

    meta: dict = {}
    if title:
        meta["title"] = title
    if hc_meta.get("subtitle"):
        meta["subtitle"] = hc_meta["subtitle"]
    if authors:
        meta["authors"] = authors
    if narrators:
        meta["narrators"] = narrators
    if series_strs:
        meta["series"] = series_strs
    if hc_meta.get("genres"):
        meta["genres"] = hc_meta["genres"]
    if hc_meta.get("published_year"):
        meta["publishedYear"] = str(hc_meta["published_year"])
    if hc_meta.get("publisher"):
        meta["publisher"] = hc_meta["publisher"]
    if hc_meta.get("description"):
        meta["description"] = hc_meta["description"]
    if hc_meta.get("isbn"):
        meta["isbn"] = hc_meta["isbn"]
    if hc_meta.get("asin"):
        meta["asin"] = hc_meta["asin"]
    if hc_meta.get("language"):
        meta["language"] = hc_meta["language"]

    dest = target_dir / "metadata.json"
    dest.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    logger.info("Wrote metadata.json to %s", dest)


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

        if src.is_dir():
            # Move whole directory contents
            for item in src.iterdir():
                dst = dest_dir / item.name
                if dst == item:
                    continue  # already there
                if item.is_file():
                    if download_client == "qbittorrent":
                        await asyncio.to_thread(shutil.copy2, str(item), str(dst))
                    else:
                        await asyncio.to_thread(shutil.move, str(item), str(dst))
        elif src.is_file():
            ext = src.suffix
            dest_file = _dedup_dest(dest_dir / f"{_sanitise_path_component(title)} - {_sanitise_path_component(author)}{ext}")
            if dest_file == src:
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
                await write_metadata_json(dest_dir, db, book_id, narrator, api_key)
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

        # Poll for match
        matched_abs_id = None
        for attempt in range(10):
            try:
                matches = await abs_svc.check_library(title, author)
                for item in matches:
                    for fmt in item.get("formats", []):
                        if fmt.get("type") == book_type:
                            matched_abs_id = item["abs_id"]
                            break
                    if matched_abs_id:
                        break
            except Exception as e:
                logger.warning("ABS check_library attempt %d failed: %s", attempt + 1, e)

            if matched_abs_id:
                break
            if attempt < 9:
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
                abs_url = f"{abs_svc.base_url}/item/{matched_abs_id}"
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
                # Soft failure — file is on disk, next library sync will find it
                await db.execute(
                    "UPDATE requests SET status='completed', updated_at=? WHERE id=?",
                    (now, request_id),
                )
                logger.warning(
                    "Request %s: ABS poll exhausted, leaving as completed for next sync",
                    request_id,
                )
            await db.commit()

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
