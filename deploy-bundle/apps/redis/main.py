# redis database example — the CRUD sample script, with a browser UI.
#
# Redis · in-memory key-value store · SET / GET / INCR / EXPIRE / DEL
#
# ARCHITECTURE / SECURITY: the database itself listens on 127.0.0.1 ONLY and is
# never exposed to the platform edge. Routing is by port, so binding a database
# to 0.0.0.0 would publish it to the internet — for a dev database with weak or
# no credentials that is a serious hole. THIS app is the only thing on a public
# port; it talks to the database over loopback and renders the result.
#
# Binds 0.0.0.0:8006 (§8). my-container-8006.example.com -> :8006.
# NOTE: :8006 is a PROPOSED port — confirm with Anthony.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = "redis"
PORT = int(os.environ.get("PORT", 8006))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

app = FastAPI(title=f"{APP_NAME} — database hello world")


def connect():
    """Open a connection. Raises with a readable message if the server is down."""

    import redis
    url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    r = redis.Redis.from_url(url, decode_responses=True)
    r.ping()  # fail fast with a clear error if the server isn't up
    return r


def server_version(r) -> str:
    """Best-effort version string. NEVER let this break the tile — it is
    cosmetic, but a bare r.info() 503s the whole page if INFO is unavailable
    (restricted build, ACL, or an emulator that omits it)."""
    try:
        return f"redis {r.info()['redis_version']}"
    except Exception:
        return "redis (version unavailable)"


def run_demo():
    """Full CRUD cycle, capturing the command and result of each step."""
    steps = []

    def step(label, cmd, result):
        steps.append({"label": label, "sql": str(cmd).strip(), "result": str(result)})

    r = connect()
    try:

        k = "disent:demo"
        r.delete(k, k + ":hits")
        step("Start clean", f'DEL {k}', "any previous demo keys removed")

        r.set(k, "hello from the redis tile")
        step("SET a key", f'SET {k} "hello from the redis tile"', "OK")

        step("GET it back", f"GET {k}", r.get(k))

        r.mset({f"{k}:a": "1", f"{k}:b": "2"})
        step("MSET several", f"MSET {k}:a 1 {k}:b 2", "OK")
        step("KEYS matching", f"KEYS {k}*", sorted(r.keys(k + "*")))

        for _ in range(3):
            r.incr(k + ":hits")
        step("INCR a counter", f"INCR {k}:hits  (x3)", r.get(k + ":hits"))

        r.expire(k, 60)
        step("EXPIRE (TTL)", f"EXPIRE {k} 60", f"TTL is now {r.ttl(k)}s")

        n = r.delete(k, k + ":a", k + ":b", k + ":hits")
        step("DEL cleanup", f"DEL {k} {k}:a {k}:b {k}:hits", f"{n} keys removed")
    finally:
        try:
            pass
        except Exception:
            pass
    return steps, server_version(r)


@app.get("/api/demo")
def api_demo() -> JSONResponse:
    try:
        steps, ver = run_demo()
        return JSONResponse({"server": ver, "steps": steps})
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=503)


@app.get("/health")
def health() -> JSONResponse:
    try:
        run_demo()
        return JSONResponse({"app": APP_NAME, "status": "ok", "db": "reachable",
                             "python": platform.python_version()})
    except Exception as e:
        return JSONResponse({"app": APP_NAME, "status": "degraded",
                             "db": f"unreachable: {type(e).__name__}",
                             "python": platform.python_version()}, status_code=503)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    try:
        steps, ver = run_demo()
        body = "\n".join(
            f'<div class="step"><div class="label">{i}. {s["label"]}</div>'
            f'<pre class="sql">{s["sql"]}</pre>'
            f'<div class="result">{s["result"]}</div></div>'
            for i, s in enumerate(steps, 1))
        note = f'<span class="ok">connected · {ver}</span>'
    except Exception as e:
        body = ('<div class="step"><div class="result" style="color:#f0a0a0">'
                f'{type(e).__name__}: {e}</div></div>')
        note = ('<span class="warn">database not reachable — the server may not be '
                'installed or running yet. The tile still renders.</span>')
    return PAGE.format(app=APP_NAME, sub='Redis · in-memory key-value store · SET / GET / INCR / EXPIRE / DEL', note=note, body=body,
                       host=HOST, port=PORT)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{app} — database hello world</title><style>
body {{ font:16px/1.5 system-ui,sans-serif; margin:0; padding:2rem 1rem; display:grid;
       place-items:start center; min-height:100vh; background:#0f1117; color:#e6e8ee; }}
.card {{ padding:2rem 2.5rem; border:1px solid #262b38; border-radius:12px;
        background:#161a23; width:min(92vw,44rem); }}
h1 {{ margin:0 0 .25rem; font-size:1.4rem; text-align:center; }}
.sub {{ text-align:center; color:#8a93a6; }}
code {{ background:#0f1117; padding:.1rem .4rem; border-radius:4px; color:#7dd3fc; }}
.note {{ text-align:center; margin-top:.6rem; font-size:.85rem; }}
.ok {{ color:#86efac; }} .warn {{ color:#fbbf24; }}
.step {{ margin-top:1.1rem; padding-top:1.1rem; border-top:1px solid #1e2330; }}
.label {{ font-weight:600; font-size:.95rem; }}
pre.sql {{ margin:.4rem 0; padding:.6rem .8rem; background:#0f1117; border-radius:8px;
          color:#7dd3fc; font-size:.82rem; overflow-x:auto; white-space:pre; }}
.result {{ color:#86efac; font-size:.85rem; font-family:ui-monospace,monospace;
          word-break:break-word; }}
.meta {{ color:#8a93a6; font-size:.85rem; margin-top:1.5rem; text-align:center; }}
</style></head><body>
  <div class="card">
    <h1>👋 hello from <code>{app}</code></h1>
    <div class="sub">{sub}</div>
    <div class="note">{note}</div>
{body}
    <div class="meta">listening on {host}:{port} ·
      <a href="/api/demo" style="color:#7dd3fc">/api/demo</a> ·
      <a href="/health" style="color:#7dd3fc">/health</a> ·
      reload to re-run the cycle<br>
      the database itself listens on 127.0.0.1 only — never exposed publicly
    </div>
  </div>
</body></html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
