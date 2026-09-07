# mcp_server AI example — MCP - Model Context Protocol server - tools exposed over a standard interface
#
# A minimal MCP server exposing two tools. Needs NO API key — the tile lists the tools and calls one directly.
#
# Pattern matches the other AI rows: a thin FastAPI wrapper so a CLI/library
# shaped framework is viewable on a port (CLAUDE.md §6), with BYOK — a key
# typed into the UI is used for that ONE request and never stored. A server
# key in .env (systemd EnvironmentFile, §8) is an optional fallback.
#
# Binds 0.0.0.0:3406 (§8). my-container-3406.example.com -> :3406.
# NOTE: :3406 is a PROPOSED port (AI 3400s block) — confirm with Anthony.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

APP_NAME = "mcp_server"
PORT = int(os.environ.get("PORT", 3406))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)
app = FastAPI(title=f"{APP_NAME} — AI hello world")
KEY_VAR = None

# The MCP server itself. Defined at import time so the tile can introspect it.
# mcp 2.0 restructured: the old `mcp.server.fastmcp.FastMCP` is gone, replaced
# by `MCPServer`. (Verified against the installed package — the 1.x FastMCP
# import in most tutorials raises ModuleNotFoundError on 2.x.)
from mcp.server.mcpserver import MCPServer

MCP = MCPServer("disent-demo")


@MCP.tool()
def add(a: int, b: int) -> int:
    """Add two integers together."""
    return a + b


@MCP.tool()
def shout(text: str) -> str:
    """Return the text uppercased with an exclamation mark."""
    return text.upper() + "!"



def key_present() -> bool:
    return True if KEY_VAR is None else bool(os.environ.get(KEY_VAR))


def run_agent(topic: str, api_key: str | None):
    """The actual framework call. Everything above/below is just plumbing."""
    import asyncio

    async def _go():
        # List the tools this server exposes, then actually call one. No model,
        # no API key — this proves the MCP surface itself works.
        tools = await MCP.list_tools()
        listing = [{"name": t.name, "description": t.description} for t in tools]
        called = await MCP.call_tool("add", {"a": 2, "b": 40})
        # mcp 2.0 returns a CallToolResult whose .content is a list of blocks.
        blocks = getattr(called, "content", None) or []
        text = getattr(blocks[0], "text", str(blocks[0])) if blocks else str(called)
        return {"tools": listing, "called": "add(a=2, b=40)", "result": text}

    return asyncio.run(_go())

class Ask(BaseModel):
    topic: str
    api_key: str | None = None  # BYOK — per-request, never persisted


@app.post("/api/run")
def run(body: Ask) -> JSONResponse:
    key = (body.api_key or "").strip() or (os.environ.get(KEY_VAR) if KEY_VAR else None)
    if KEY_VAR and not key:
        return JSONResponse(
            {"error": f"No API key: paste yours in the key field (used per-request, "
                      f"never stored), or set {KEY_VAR} in .env."},
            status_code=503,
        )
    topic = body.topic.strip()
    if not topic:
        return JSONResponse({"error": "topic is required"}, status_code=400)
    try:
        return JSONResponse({"answer": run_agent(topic, key)})
    except Exception as e:  # surface framework errors readably in the tile
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({
        "app": APP_NAME, "status": "ok",
        "key_required": KEY_VAR is not None,
        "key_present": key_present(),
        "python": platform.python_version(),
    })


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    if KEY_VAR is None:
        status = '<span class="ok">no API key needed — this row runs standalone</span>'
        keyfield = ""
    elif key_present():
        status = '<span class="ok">server key configured — run it (or use your own key)</span>'
        keyfield = KEYFIELD
    else:
        status = '<span class="warn">no server key — paste your own below (per-request, never stored)</span>'
        keyfield = KEYFIELD
    return PAGE.format(app=APP_NAME, blurb='MCP · Model Context Protocol server · tools exposed over a standard interface', status=status,
                       keyfield=keyfield, host=HOST, port=PORT)


KEYFIELD = ('<div class="row"><input id="key" type="password" autocomplete="off" '
            'placeholder="your API key (optional — per-request, never stored)" '
            'aria-label="api key"></div>')

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{app} — AI hello world</title><style>
body {{ font:16px/1.5 system-ui,sans-serif; margin:0; display:grid; place-items:center;
       min-height:100vh; background:#0f1117; color:#e6e8ee; }}
.card {{ text-align:center; padding:2rem 2.5rem; border:1px solid #262b38;
       border-radius:12px; background:#161a23; width:min(92vw,36rem); }}
h1 {{ margin:0 0 .25rem; font-size:1.4rem; }}
code {{ background:#0f1117; padding:.1rem .4rem; border-radius:4px; color:#7dd3fc; }}
.meta {{ color:#8a93a6; font-size:.85rem; margin-top:1rem; }}
.ok {{ color:#86efac; }} .warn {{ color:#fbbf24; }}
.row {{ display:flex; gap:.5rem; margin-top:.6rem; }}
input {{ flex:1; padding:.5rem .75rem; border-radius:8px; border:1px solid #262b38;
        background:#0f1117; color:#e6e8ee; font:inherit; }}
button {{ padding:.5rem 1rem; border-radius:8px; border:1px solid #2b6cb0;
         background:#1a2433; color:#7dd3fc; font:inherit; cursor:pointer; }}
button:hover {{ background:#22304a; }}
#out {{ margin-top:1rem; padding:.75rem 1rem; border-radius:8px; border:1px solid #2b6cb0;
       background:#101725; color:#7dd3fc; font-size:.9rem; text-align:left;
       display:none; white-space:pre-wrap; }}
</style></head><body>
  <div class="card">
    <h1>👋 hello from <code>{app}</code></h1>
    <div>{blurb}</div>
    <div class="meta">{status}</div>
    <form onsubmit="go(event)">
      <div class="row">
        <input id="q" placeholder="give it a topic…" aria-label="topic" value="the Model Context Protocol">
        <button type="submit">run</button>
      </div>
      {keyfield}
    </form>
    <div id="out"></div>
    <div class="meta">listening on {host}:{port} ·
      <a href="/health" style="color:#7dd3fc">/health</a></div>
  </div>
<script>
async function go(e) {{
  e.preventDefault();
  const out = document.getElementById("out");
  out.style.display = "block"; out.textContent = "running (can take a moment)…";
  const k = document.getElementById("key");
  try {{
    const r = await fetch("/api/run", {{ method:"POST",
      headers:{{ "content-type":"application/json" }},
      body: JSON.stringify({{ topic: document.getElementById("q").value,
                            api_key: k ? (k.value || null) : null }}) }});
    const d = await r.json();
    out.textContent = typeof (d.answer ?? d.error) === "string"
      ? (d.answer ?? d.error) : JSON.stringify(d.answer ?? d.error, null, 2);
  }} catch (err) {{ out.textContent = "request failed: " + err; }}
}}
</script></body></html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
