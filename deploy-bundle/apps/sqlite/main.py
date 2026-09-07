# sqlite database example — the CRUD sample script, with a browser UI.
#
# The other four database rows (postgres, mysql, mongodb, redis) are
# client-server databases that Infra provisions as containers, browsed through
# CloudBeaver. SQLite is the odd one out: it is a FILE, not a server. Python's
# stdlib `sqlite3` talks to it directly, so this row needs no provisioning, no
# container, and no credentials — which is why it can ship while the other four
# wait.
#
# It demonstrates the full CRUD cycle the tracker asks for (create a table,
# insert rows, read them, update, delete, drop) and shows each step's SQL and
# result in the page, so the tile teaches rather than just proving liveness.
#
# Binds TCP 8005 on 0.0.0.0 (§8). my-container-8005.example.com -> :8005.
# NOTE: :8005 is a PROPOSED port (continues the 800x app block) — confirm.

import os
import platform
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

APP_NAME = "sqlite"
PORT = int(os.environ.get("PORT", 8005))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)
DB_PATH = Path(__file__).parent / "demo.db"

app = FastAPI(title=f"{APP_NAME} — database hello world")


def run_demo() -> list[dict]:
    """Run a full CRUD cycle, capturing the SQL and result of each step.

    Uses a throwaway table so the demo is idempotent — you can reload the page
    as many times as you like and always see the same clean sequence.
    """
    steps: list[dict] = []

    def step(label: str, sql: str, result) -> None:
        steps.append({"label": label, "sql": sql.strip(), "result": result})

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        sql = "DROP TABLE IF EXISTS fruit"
        cur.execute(sql)
        step("Start clean", sql, "table dropped if it existed")

        sql = """CREATE TABLE fruit (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL UNIQUE,
    count INTEGER NOT NULL DEFAULT 0
)"""
        cur.execute(sql)
        step("CREATE a table", sql, "table 'fruit' created")

        sql = "INSERT INTO fruit (name, count) VALUES (?, ?)"
        rows = [("apple", 3), ("banana", 7), ("cherry", 12)]
        cur.executemany(sql, rows)
        step("INSERT rows", sql, f"{cur.rowcount} rows inserted: {rows}")

        sql = "SELECT id, name, count FROM fruit ORDER BY count DESC"
        got = [dict(r) for r in cur.execute(sql).fetchall()]
        step("SELECT (read)", sql, got)

        sql = "UPDATE fruit SET count = count + 10 WHERE name = ?"
        cur.execute(sql, ("apple",))
        step("UPDATE a row", sql, f"{cur.rowcount} row updated (apple +10)")

        sql = "DELETE FROM fruit WHERE count < ?"
        cur.execute(sql, (10,))
        step("DELETE rows", sql, f"{cur.rowcount} row(s) with count < 10 removed")

        sql = "SELECT id, name, count FROM fruit ORDER BY count DESC"
        final = [dict(r) for r in cur.execute(sql).fetchall()]
        step("SELECT (final state)", sql, final)

    return steps


@app.get("/api/demo")
def api_demo() -> JSONResponse:
    return JSONResponse({"steps": run_demo(), "db_file": str(DB_PATH)})


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "app": APP_NAME,
            "status": "ok",
            "sqlite_version": sqlite3.sqlite_version,
            "python": platform.python_version(),
        }
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    steps = run_demo()
    blocks = "\n".join(
        f"""      <div class="step">
        <div class="label">{i}. {s['label']}</div>
        <pre class="sql">{s['sql']}</pre>
        <div class="result">{s['result']}</div>
      </div>"""
        for i, s in enumerate(steps, 1)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} — database hello world</title>
  <style>
    body {{ font: 16px/1.5 system-ui, sans-serif; margin: 0; padding: 2rem 1rem;
           display: grid; place-items: start center; min-height: 100vh;
           background: #0f1117; color: #e6e8ee; }}
    .card {{ padding: 2rem 2.5rem; border: 1px solid #262b38; border-radius: 12px;
            background: #161a23; width: min(92vw, 44rem); }}
    h1 {{ margin: 0 0 .25rem; font-size: 1.4rem; text-align: center; }}
    .sub {{ text-align: center; color: #8a93a6; }}
    code {{ background: #0f1117; padding: .1rem .4rem; border-radius: 4px; color: #7dd3fc; }}
    .step {{ margin-top: 1.1rem; padding-top: 1.1rem; border-top: 1px solid #1e2330; }}
    .label {{ color: #e6e8ee; font-weight: 600; font-size: .95rem; }}
    pre.sql {{ margin: .4rem 0; padding: .6rem .8rem; background: #0f1117;
              border-radius: 8px; color: #7dd3fc; font-size: .82rem;
              overflow-x: auto; white-space: pre; }}
    .result {{ color: #86efac; font-size: .85rem; font-family: ui-monospace, monospace;
              word-break: break-word; }}
    .meta {{ color: #8a93a6; font-size: .85rem; margin-top: 1.5rem; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>{APP_NAME}</code></h1>
    <div class="sub">SQLite · a database in a single file · Python stdlib, no server</div>
{blocks}
    <div class="meta">
      sqlite {sqlite3.sqlite_version} · python {platform.python_version()} ·
      listening on {HOST}:{PORT}<br>
      <a href="/api/demo" style="color:#7dd3fc">/api/demo</a> ·
      <a href="/health" style="color:#7dd3fc">/health</a> ·
      reload to re-run the whole cycle
    </div>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
