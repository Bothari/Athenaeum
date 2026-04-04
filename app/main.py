import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import get_db, init_db

logger = logging.getLogger(__name__)

app = FastAPI(title="Athenaeum")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialised")


@app.get("/healthz", include_in_schema=False)
async def healthz():
    try:
        async with get_db() as db:
            await db.execute("SELECT 1")
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=503, content={"ok": False, "error": str(e)})


@app.get("/api/status")
async def api_status():
    async with get_db() as db:
        books_row = await (await db.execute("SELECT COUNT(*) FROM books")).fetchone()
        authors_row = await (await db.execute("SELECT COUNT(*) FROM authors")).fetchone()
        series_row = await (await db.execute("SELECT COUNT(*) FROM series")).fetchone()

        statuses = [
            "requested", "monitored", "snatched", "downloading",
            "downloaded", "merging", "organizing", "in_library", "failed",
        ]
        requests = {}
        for status in statuses:
            row = await (
                await db.execute(
                    "SELECT COUNT(*) FROM requests WHERE status = ?", (status,)
                )
            ).fetchone()
            requests[status] = row[0]

    return {
        "books": books_row[0],
        "authors": authors_row[0],
        "series": series_row[0],
        "requests": requests,
    }


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})
