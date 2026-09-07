# fastapi environment example — a minimal FastAPI backend, no database.
# (This is the "backend" row for FastAPI; fullstack/DB variants live in their
#  own rows.)
#
# Binds TCP 8000 on 0.0.0.0. The platform routes the public subdomain by PORT
# (my-container-8000.example.com -> container:8000), so the app MUST listen
# on 0.0.0.0, not 127.0.0.1 — otherwise the edge gets a 502. See CLAUDE.md §2/§8.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = "fastapi"
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

app = FastAPI(title=f"{APP_NAME} — hello world")


def page() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} — hello world</title>
  <style>
    body {{ font: 16px/1.5 system-ui, sans-serif; margin: 0;
           display: grid; place-items: center; min-height: 100vh;
           background: #0f1117; color: #e6e8ee; }}
    .card {{ text-align: center; padding: 2rem 2.5rem; border: 1px solid #262b38;
            border-radius: 12px; background: #161a23; }}
    h1 {{ margin: 0 0 .25rem; font-size: 1.4rem; }}
    code {{ background: #0f1117; padding: .1rem .4rem; border-radius: 4px;
           color: #7dd3fc; }}
    .meta {{ color: #8a93a6; font-size: .85rem; margin-top: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>{APP_NAME}</code></h1>
    <div>Python · FastAPI · no database</div>
    <div class="meta">
      served by {platform.node()} · python {platform.python_version()}<br>
      listening on {HOST}:{PORT} ·
      <a href="/health" style="color:#7dd3fc">/health</a> ·
      <a href="/docs" style="color:#7dd3fc">/docs</a>
    </div>
  </div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return page()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {"app": APP_NAME, "status": "ok", "python": platform.python_version()}
    )


if __name__ == "__main__":
    # Run directly with `python main.py` (mirrors the nodejs example's
    # `npm start`). uvicorn is the ASGI server FastAPI runs on.
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
