import asyncio
import logging

logger = logging.getLogger(__name__)

# event_type -> list of item dicts accumulated during the window
_batches: dict[str, list] = {}
# event_type -> asyncio.Task sleeping until flush
_batch_tasks: dict[str, asyncio.Task] = {}
_lock = asyncio.Lock()


async def _flush(event_type: str, window: int):
    await asyncio.sleep(window)
    async with _lock:
        items = _batches.pop(event_type, [])
        _batch_tasks.pop(event_type, None)
    if not items:
        return
    await _send(event_type, items)


async def notify(event_type: str, item: dict):
    """Queue item for batched delivery. event_type: 'pending' | 'in_library'"""
    from ..settings import get_settings
    settings = await get_settings()
    cfg = settings.get("notifications", {})
    urls = cfg.get("urls", "").strip()
    if not urls:
        return
    window = int(cfg.get("batch_window", 60))

    async with _lock:
        if event_type not in _batches:
            _batches[event_type] = []
        _batches[event_type].append(item)
        if event_type not in _batch_tasks or _batch_tasks[event_type].done():
            _batch_tasks[event_type] = asyncio.create_task(_flush(event_type, window))


async def _send(event_type: str, items: list):
    from ..settings import get_settings
    settings = await get_settings()
    cfg = settings.get("notifications", {})
    urls = cfg.get("urls", "").strip()
    if not urls:
        return

    try:
        import apprise
        ap = apprise.Apprise()
        for url in urls.splitlines():
            url = url.strip()
            if url:
                ap.add(url)

        if event_type == "pending":
            count = len(items)
            if count == 1:
                item = items[0]
                title = "New request pending approval"
                body = f"{item['title']} by {item['author']} ({item['type']})"
            else:
                title = f"{count} requests pending approval"
                lines = [f"- {i['title']} by {i['author']} ({i['type']})" for i in items]
                body = "\n".join(lines)
        elif event_type == "in_library":
            count = len(items)
            if count == 1:
                item = items[0]
                title = "Book added to library"
                body = f"{item['title']} by {item['author']} ({item['type']})"
            else:
                title = f"{count} books added to library"
                lines = [f"- {i['title']} by {i['author']} ({i['type']})" for i in items]
                body = "\n".join(lines)
        else:
            return

        await ap.async_notify(body=body, title=title)
    except Exception as e:
        logger.warning("Notification send failed (%s): %s", event_type, e)


async def send_test(urls: str):
    """Send a test notification to the given URLs. Raises on failure."""
    import apprise
    ap = apprise.Apprise()
    for url in urls.splitlines():
        url = url.strip()
        if url:
            ap.add(url)
    if not ap:
        raise ValueError("No valid notification URLs provided")
    ok = await ap.async_notify(body="This is a test notification from Athenaeum.", title="Athenaeum")
    if not ok:
        raise ValueError("Notification delivery failed — check your URLs")
