# python environment example — bare Python, standard library only.
#
# The Python counterpart to the `nodejs` row: no framework, no dependencies,
# nothing to install. Just http.server from the stdlib. (FastAPI, Flask and
# Django each have their own row — this one deliberately uses none of them.)
#
# Binds TCP 3008 on 0.0.0.0 (§8). my-container-3008.example.com -> :3008.
# NOTE: :3008 is a PROPOSED port (continues the 300x block after c_cpp 3007) —
# confirm with Anthony.
#
# Run:  python3 server.py       (no venv, no pip — stdlib only)

import json
import os
import platform
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "python"
PORT = int(os.environ.get("PORT", 3008))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)


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
    <div>bare Python · stdlib http.server · no framework, no dependencies</div>
    <div class="meta">
      served by {socket.gethostname()} · python {platform.python_version()}<br>
      listening on {HOST}:{PORT} ·
      <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, ctype: str) -> None:
        raw = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path == "/health":
            self._send(
                json.dumps(
                    {"app": APP_NAME, "status": "ok", "python": platform.python_version()}
                ),
                "application/json",
            )
        else:
            self._send(page(), "text/html; charset=utf-8")

    def log_message(self, fmt, *args):  # keep journald output tidy
        pass


if __name__ == "__main__":
    print(f"[{APP_NAME}] listening on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
