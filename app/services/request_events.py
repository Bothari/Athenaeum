import json
import uuid
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


async def log_request_event(db, request_id: str, event_type: str, detail: dict = None, book_id: str = None):
    """Insert a request_events row.

    book_id is looked up from the requests table if not provided — callers that
    already have it should pass it to avoid the extra query.
    Events are kept even after the request is deleted (no FK constraint).
    """
    if not book_id:
        row = await (
            await db.execute("SELECT book_id FROM requests WHERE id = ?", (request_id,))
        ).fetchone()
        book_id = row["book_id"] if row else ""
    await db.execute(
        """INSERT INTO request_events (id, request_id, book_id, event_type, detail, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), request_id, book_id, event_type, json.dumps(detail or {}), _now()),
    )


async def set_request_status(db, request_id: str, new_status: str, now: str, book_id: str = None, extra: dict = None):
    """UPDATE requests.status and log the state_change event in one call.

    Drop-in replacement for bare UPDATE requests SET status=? calls.
    Pass book_id when already known to avoid the lookup SELECT.
    """
    old_row = await (
        await db.execute("SELECT status, book_id FROM requests WHERE id = ?", (request_id,))
    ).fetchone()
    await db.execute(
        "UPDATE requests SET status=?, updated_at=? WHERE id=?",
        (new_status, now, request_id),
    )
    bid = book_id or (old_row["book_id"] if old_row else "")
    ev = {"from": old_row["status"] if old_row else "", "to": new_status}
    if extra:
        ev.update(extra)
    await log_request_event(db, request_id, "state_change", ev, book_id=bid)
