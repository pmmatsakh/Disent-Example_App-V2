# flask environment example — a minimal Flask backend, no database.
# (This is the "backend" row for Flask; fullstack/DB variants live elsewhere.)
#
# Binds TCP 8001 on 0.0.0.0. The platform routes the public subdomain by PORT
# (my-container-8001.example.com -> container:8001), so the app MUST listen
# on 0.0.0.0, not 127.0.0.1 — otherwise the edge gets a 502. See CLAUDE.md §2/§8.

import os
import platform

from flask import Flask, jsonify

APP_NAME = "flask"
PORT = int(os.environ.get("PORT", 8001))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

app = Flask(__name__)


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
    <div>Python · Flask · no database</div>
    <div class="meta">
      served by {platform.node()} · python {platform.python_version()}<br>
      listening on {HOST}:{PORT} ·
      <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>"""


@app.get("/")
def root():
    return page()


@app.get("/health")
def health():
    return jsonify(app=APP_NAME, status="ok", python=platform.python_version())


if __name__ == "__main__":
    # `python app.py` runs Flask's built-in dev server (fine for a hello-world
    # tile). On the container a production server would front this, but the
    # dev server is enough to prove the capability end-to-end.
    app.run(host=HOST, port=PORT)
