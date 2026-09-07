# postgres database example — the CRUD sample script, with a browser UI.
#
# PostgreSQL · relational database · CREATE / INSERT / SELECT / UPDATE / DELETE
#
# ARCHITECTURE / SECURITY: the database itself listens on 127.0.0.1 ONLY and is
# never exposed to the platform edge. Routing is by port, so binding a database
# to 0.0.0.0 would publish it to the internet — for a dev database with weak or
# no credentials that is a serious hole. THIS app is the only thing on a public
# port; it talks to the database over loopback and renders the result.
#
# Binds 0.0.0.0:8007 (§8). my-container-8007.example.com -> :8007.
# NOTE: :8007 is a PROPOSED port — confirm with Anthony.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = "postgres"
PORT = int(os.environ.get("PORT", 8007))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

app = FastAPI(title=f"{APP_NAME} — database hello world")


def connect():
    """Open a connection. Raises with a readable message if the server is down."""

    import psycopg
    dsn = os.environ.get("PG_DSN", "postgresql://disent:disent@127.0.0.1:5432/disent")
    conn = psycopg.connect(dsn, connect_timeout=5)
    conn.autocommit = True
    r = conn.cursor()
    return r, conn


def server_version(conn) -> str:
    """Best-effort version string. NEVER let this break the tile — it is
    cosmetic, but an unguarded lookup 503s the whole page even when every CRUD
    step succeeded. (Learned from the redis tile's r.info() on 2026-08-12.)"""
    try:
        return f"postgres {conn.info.server_version // 10000}.{conn.info.server_version % 100}"
    except Exception:
        return "postgres (version unavailable)"


def run_demo():
    """Full CRUD cycle, capturing the command and result of each step."""
    steps = []

    def step(label, cmd, result):
        steps.append({"label": label, "sql": str(cmd).strip(), "result": str(result)})

    r, conn = connect()
    ver = "unknown"
    try:

        r.execute("DROP TABLE IF EXISTS fruit")
        step("Start clean", "DROP TABLE IF EXISTS fruit", "dropped if it existed")

        r.execute("""CREATE TABLE fruit (
    id    SERIAL PRIMARY KEY,
    name  TEXT    NOT NULL UNIQUE,
    count INTEGER NOT NULL DEFAULT 0
)""")
        step("CREATE a table", "CREATE TABLE fruit (id SERIAL PRIMARY KEY, name TEXT UNIQUE, count INT)", "table created")

        r.executemany("INSERT INTO fruit (name, count) VALUES (%s, %s)",
                      [("apple", 3), ("banana", 7), ("cherry", 12)])
        step("INSERT rows", "INSERT INTO fruit (name, count) VALUES (%s, %s)", "3 rows inserted")

        r.execute("SELECT id, name, count FROM fruit ORDER BY count DESC")
        step("SELECT (read)", "SELECT id, name, count FROM fruit ORDER BY count DESC", r.fetchall())

        r.execute("UPDATE fruit SET count = count + 10 WHERE name = %s", ("apple",))
        step("UPDATE a row", "UPDATE fruit SET count = count + 10 WHERE name = 'apple'", f"{r.rowcount} row updated")

        r.execute("DELETE FROM fruit WHERE count < %s", (10,))
        step("DELETE rows", "DELETE FROM fruit WHERE count < 10", f"{r.rowcount} row(s) removed")

        r.execute("SELECT id, name, count FROM fruit ORDER BY count DESC")
        step("SELECT (final)", "SELECT id, name, count FROM fruit ORDER BY count DESC", r.fetchall())
        # Read the version while the connection is STILL OPEN. The finally
        # block below closes it, and both psycopg and PyMySQL raise on a closed
        # connection — which previously surfaced as "version unavailable" even
        # though every CRUD step had succeeded.
        ver = server_version(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return steps, ver


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
    return PAGE.format(app=APP_NAME, sub='PostgreSQL · relational database · CREATE / INSERT / SELECT / UPDATE / DELETE', note=note, body=body,
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
