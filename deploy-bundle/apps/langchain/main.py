# langchain AI example — a minimal LangChain "hello world" with a browser UI.
#
# The capability this tile proves: a LangChain chain (prompt template -> Claude
# model -> output parser) runs end-to-end. The FastAPI wrapper exists only so
# the CLI-shaped framework is viewable on a port (CLAUDE.md §6: "most are CLI
# scripts needing a thin shared FastAPI wrapper").
#
# The Anthropic API key is loaded from the environment (.env via systemd
# EnvironmentFile on the container — CLAUDE.md §8; never hard-coded). With no
# key the tile still renders and /health reports key_present=false, so the app
# is verifiable before credentials exist.
#
# Binds 0.0.0.0:3401 (§8). my-container-3401.example.com -> :3401.
# NOTE: :3401 is a PROPOSED port (AI 3400s block) — confirm with Anthony.

import os
import platform

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

APP_NAME = "langchain"
PORT = int(os.environ.get("PORT", 3401))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)
MODEL = "claude-opus-4-8"  # current Opus model per the Anthropic docs

app = FastAPI(title=f"{APP_NAME} — AI hello world")


def key_present() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def build_chain(api_key: str | None):
    """A minimal LCEL chain: prompt template -> Claude -> string output.

    BYOK: if the request carries a key it is used for THIS call only — never
    stored, logged, or written anywhere server-side. The server .env key (if
    set) is an optional fallback for internal/demo mode.
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a friendly assistant. Answer in one short sentence."),
            ("human", "{question}"),
        ]
    )
    kwargs = {"model": MODEL, "max_tokens": 256}
    if api_key:
        kwargs["api_key"] = api_key
    model = ChatAnthropic(**kwargs)
    return prompt | model | StrOutputParser()


class Ask(BaseModel):
    question: str
    api_key: str | None = None  # BYOK — per-request, never persisted


@app.post("/api/ask")
def ask(body: Ask) -> JSONResponse:
    user_key = (body.api_key or "").strip() or None
    if not user_key and not key_present():
        return JSONResponse(
            {"error": "No API key: paste yours in the key field (used per-request, "
                      "never stored), or set ANTHROPIC_API_KEY in .env."},
            status_code=503,
        )
    q = body.question.strip()
    if not q:
        return JSONResponse({"error": "question is required"}, status_code=400)
    try:
        answer = build_chain(user_key).invoke({"question": q})
        return JSONResponse({"answer": answer, "model": MODEL})
    except Exception as e:  # surface API errors readably in the tile
        return JSONResponse({"error": str(e)}, status_code=502)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "app": APP_NAME,
            "status": "ok",
            "key_present": key_present(),
            "model": MODEL,
            "python": platform.python_version(),
        }
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    ready = key_present()
    status_html = (
        '<span class="ok">server key configured — ask away (or use your own key)</span>'
        if ready
        else '<span class="warn">no server key — paste your own below (used per-request, never stored)</span>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{APP_NAME} — AI hello world</title>
  <style>
    body {{ font: 16px/1.5 system-ui, sans-serif; margin: 0;
           display: grid; place-items: center; min-height: 100vh;
           background: #0f1117; color: #e6e8ee; }}
    .card {{ text-align: center; padding: 2rem 2.5rem; border: 1px solid #262b38;
            border-radius: 12px; background: #161a23; width: min(90vw, 34rem); }}
    h1 {{ margin: 0 0 .25rem; font-size: 1.4rem; }}
    code {{ background: #0f1117; padding: .1rem .4rem; border-radius: 4px;
           color: #7dd3fc; }}
    .meta {{ color: #8a93a6; font-size: .85rem; margin-top: 1rem; }}
    .ok {{ color: #86efac; }} .warn {{ color: #fbbf24; }}
    .row {{ display: flex; gap: .5rem; margin-top: 1rem; }}
    input {{ flex: 1; padding: .5rem .75rem; border-radius: 8px;
            border: 1px solid #262b38; background: #0f1117; color: #e6e8ee; font: inherit; }}
    button {{ padding: .5rem 1rem; border-radius: 8px; border: 1px solid #2b6cb0;
             background: #1a2433; color: #7dd3fc; font: inherit; cursor: pointer; }}
    button:hover {{ background: #22304a; }}
    #out {{ margin-top: 1rem; padding: .75rem 1rem; border-radius: 8px;
           border: 1px solid #2b6cb0; background: #101725; color: #7dd3fc;
           font-size: .9rem; text-align: left; display: none; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>{APP_NAME}</code></h1>
    <div>LangChain · prompt → Claude ({MODEL}) → parser</div>
    <div class="meta">{status_html}</div>
    <form onsubmit="ask(event)">
      <div class="row">
        <input id="q" placeholder="ask the chain anything…" aria-label="question">
        <button type="submit">ask</button>
      </div>
      <div class="row">
        <input id="key" type="password" autocomplete="off"
               placeholder="your Anthropic API key (optional — per-request, never stored)"
               aria-label="api key">
      </div>
    </form>
    <div id="out"></div>
    <div class="meta">listening on {HOST}:{PORT} ·
      <a href="/health" style="color:#7dd3fc">/health</a></div>
  </div>
  <script>
    async function ask(e) {{
      e.preventDefault();
      const out = document.getElementById("out");
      out.style.display = "block"; out.textContent = "thinking…";
      try {{
        const r = await fetch("/api/ask", {{ method: "POST",
          headers: {{ "content-type": "application/json" }},
          body: JSON.stringify({{ question: document.getElementById("q").value,
                                  api_key: document.getElementById("key").value || null }}) }});
        const d = await r.json();
        out.textContent = d.answer || d.error;
      }} catch (err) {{ out.textContent = "request failed: " + err; }}
    }}
  </script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
