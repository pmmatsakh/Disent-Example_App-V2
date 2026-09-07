# fastapi_react_sqlite fullstack example — React + FastAPI + SQLite, ONE port.
#
# Adds PERSISTENCE to the fullstack pattern: the React UI reads and writes a
# list of messages through /api/*, and FastAPI stores them in a SQLite file
# (data.db) next to this script. Reload the page — the data is still there,
# because it lives in the database, not in memory.
#
# SQLite needs NO server and NO infra (it's Python's stdlib `sqlite3` writing to
# a local file), so unlike the client-server DB rows this one is buildable and
# deployable today. Binds 0.0.0.0:8003 (§8). :8003 is PROPOSED — confirm.

import os
import platform
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_NAME = "fastapi_react_sqlite"
PORT = int(os.environ.get("PORT", 8003))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

BASE = Path(__file__).parent
DIST = (BASE.parent / "frontend" / "dist").resolve()
DB_PATH = BASE / "data.db"

app = FastAPI(title=f"{APP_NAME} — fullstack + persistence")


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "text TEXT NOT NULL,"
            "created TEXT NOT NULL DEFAULT (datetime('now')))"
        )


init_db()


class NewMessage(BaseModel):
    text: str


# --- API routes (registered BEFORE the static mount so they win) -------------
@app.get("/api/messages")
def list_messages() -> JSONResponse:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, text, created FROM messages ORDER BY id DESC"
        ).fetchall()
    return JSONResponse([dict(r) for r in rows])


@app.post("/api/messages")
def add_message(msg: NewMessage) -> JSONResponse:
    text = msg.text.strip()
    if not text:
        return JSONResponse({"error": "text is required"}, status_code=400)
    with db() as conn:
        cur = conn.execute("INSERT INTO messages (text) VALUES (?)", (text,))
        row = conn.execute(
            "SELECT id, text, created FROM messages WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return JSONResponse(dict(row), status_code=201)


@app.get("/api/health")
def health() -> JSONResponse:
    with db() as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM messages").fetchone()
    return JSONResponse(
        {"app": APP_NAME, "status": "ok", "messages": count, "python": platform.python_version()}
    )


# --- Static React app (mounted LAST; catches "/" and asset paths) ------------
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(DIST), html=True), name="static")
else:

    @app.get("/", response_class=HTMLResponse)
    def missing_build() -> str:
        return (
            "<h1>frontend not built yet</h1>"
            "<p>Run <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, "
            "then restart this server.</p>"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
