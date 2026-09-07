# fastapi_react fullstack example — ONE port, no CORS.
#
# The pattern: FastAPI serves a JSON API under /api/*, AND serves the compiled
# React app (frontend/dist) for everything else. Because the page and the API
# come from the same origin/port, the browser makes plain same-origin fetches —
# no CORS, no second subdomain. This is the cleanest shape for the platform's
# port-based routing (CLAUDE.md §2): one app, one port, one subdomain.
#
# Binds TCP 8002 on 0.0.0.0 (§8). my-container-8002.example.com -> :8002.
# NOTE: :8002 is a PROPOSED port (fullstack; §6 floats a 3300s block) — confirm.
#
# Build the frontend first (`cd ../frontend && npm install && npm run build`),
# which emits frontend/dist. Then run this. If dist is missing you'll get a
# clear message at / instead of a stack trace.

import os
import platform
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

APP_NAME = "fastapi_react"
PORT = int(os.environ.get("PORT", 8002))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

DIST = (Path(__file__).parent.parent / "frontend" / "dist").resolve()

app = FastAPI(title=f"{APP_NAME} — fullstack hello world")


# --- API routes (registered BEFORE the static mount so they win) -------------
@app.get("/api/hello")
def api_hello() -> JSONResponse:
    return JSONResponse(
        {
            "message": "hello from the FastAPI backend",
            "python": platform.python_version(),
            "served_by": platform.node(),
        }
    )


@app.get("/api/health")
def api_health() -> JSONResponse:
    return JSONResponse({"app": APP_NAME, "status": "ok"})


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
