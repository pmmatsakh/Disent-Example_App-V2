# autogen AI example — AutoGen - Microsoft AgentChat - AssistantAgent.run()
#
# Microsoft AutoGen AgentChat: a single AssistantAgent answers a task.
#
# Pattern matches the other AI rows: a thin FastAPI wrapper so a CLI/library
# shaped framework is viewable on a port (CLAUDE.md §6), with BYOK — a key
# typed into the UI is used for that ONE request and never stored.
#
# Binds 0.0.0.0:3405 (§8). my-container-3405.example.com -> :3405.
# NOTE: :3405 is a PROPOSED port (AI 3400s block) — confirm with Anthony.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

APP_NAME = "autogen"
PORT = int(os.environ.get("PORT", 3405))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)
app = FastAPI(title=f"{APP_NAME} — AI hello world")
KEY_VAR = 'OPENAI_API_KEY'


def run_agent(topic: str, api_key: str):
    """The actual framework call. Everything above/below is just plumbing."""
    import asyncio
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient

    async def _go():
        client = OpenAIChatCompletionClient(model="gpt-4.1", api_key=api_key)
        agent = AssistantAgent(
            "assistant", model_client=client,
            system_message="Answer in one short sentence. No preamble.",
        )
        result = await agent.run(task=topic)
        await client.close()
        # The last message in the conversation is the agent's reply.
        return result.messages[-1].content if result.messages else "(no reply)"

    return asyncio.run(_go())

class Ask(BaseModel):
    topic: str
    api_key: str | None = None  # BYOK — per-request, never persisted


@app.post("/api/run")
def run(body: Ask) -> JSONResponse:
    key = (body.api_key or "").strip()
    if KEY_VAR and not key:
        return JSONResponse(
            {"error": f"No API key: paste yours in the key field (used per-request, "
                      f"never stored)."},
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
        "key_mode": "per-request BYOK",
        "python": platform.python_version(),
    })


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    if KEY_VAR is None:
        status = '<span class="ok">no API key needed — this row runs standalone</span>'
        keyfield = ""
    else:
        status = '<span class="warn">paste your key below (per-request, never stored)</span>'
        keyfield = KEYFIELD
    return PAGE.format(app=APP_NAME, blurb='AutoGen · Microsoft AgentChat · AssistantAgent.run()', status=status,
                       keyfield=keyfield, host=HOST, port=PORT)


KEYFIELD = ('<div class="row"><input id="key" type="password" autocomplete="off" '
            'placeholder="your API key (required — per-request, never stored)" '
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
