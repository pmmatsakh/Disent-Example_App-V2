# claude_code AI example — Claude Code (the CLI agent) behind a thin web tile.
#
# The capability this tile proves: the Claude Code CLI is installed and can run
# a prompt headlessly (`claude -p "..."`), which is the foundation the
# "skills file" scaffolder row builds on (CLAUDE.md §1: the corpus + a skills
# file that lets an AI generate new Disent projects). See SKILL.md next to this
# file — that is the scaffolder instruction set this row exists to carry.
#
# Auth: Claude Code uses its own login (`claude login`) or ANTHROPIC_API_KEY.
# With neither, the tile still renders and reports status honestly.
#
# Binds 0.0.0.0:3402 (§8). my-container-3402.example.com -> :3402.
# NOTE: :3402 is a PROPOSED port (AI 3400s block) — confirm with Anthony.

import os
import platform
import shutil
import subprocess

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

APP_NAME = "claude_code"
PORT = int(os.environ.get("PORT", 3402))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

app = FastAPI(title=f"{APP_NAME} — AI hello world")


# systemd's PATH does not include nvm, and /usr/bin/node is the old Node 18 —
# the CLIs are installed under the nvm Node 22 prefix. Resolve explicitly.
NVM_BIN = "/root/.nvm/versions/node/v22.22.2/bin"


def find_cli(name: str) -> str | None:
    cand = os.path.join(NVM_BIN, name)
    if os.path.isfile(cand) and os.access(cand, os.X_OK):
        return cand
    return shutil.which(name)


def cli_status() -> dict:
    path = find_cli("claude")
    version = None
    if path:
        try:
            # Use the RESOLVED path, not the bare name — systemd's PATH has
            # neither nvm nor a modern node, so "claude" is unfindable there
            # even though find_cli() located the binary a line earlier.
            version = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=15
            ).stdout.strip()
        except Exception:
            version = "installed (version check failed)"
    return {
        "cli_installed": bool(path),
        "cli_version": version,
        "key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


class Ask(BaseModel):
    prompt: str
    api_key: str | None = None  # BYOK — per-request, never persisted


@app.post("/api/run")
def run(body: Ask) -> JSONResponse:
    st = cli_status()
    if not st["cli_installed"]:
        return JSONResponse(
            {"error": "claude CLI not installed. `npm install -g @anthropic-ai/claude-code`"},
            status_code=503,
        )
    p = body.prompt.strip()
    if not p:
        return JSONResponse({"error": "prompt is required"}, status_code=400)
    # BYOK: a request-supplied key is injected into THIS subprocess's env only —
    # never stored, logged, or exported to the server process.
    env = os.environ.copy()
    user_key = (body.api_key or "").strip()
    if user_key:
        env["ANTHROPIC_API_KEY"] = user_key
    try:
        # -p = print mode (headless, non-interactive). 120s guard.
        out = subprocess.run(
            [find_cli("claude"), "-p", p], capture_output=True, text=True, timeout=120, env=env
        )
        text = out.stdout.strip()
        # The CLI can exit 0 while reporting an auth problem on stdout — catch it.
        if out.returncode != 0 or "Not logged in" in text:
            return JSONResponse(
                {
                    "error": (out.stderr.strip() or text or "claude failed")
                    + " — run `claude login` or set ANTHROPIC_API_KEY in .env."
                },
                status_code=502,
            )
        return JSONResponse({"answer": text})
    except subprocess.TimeoutExpired:
        return JSONResponse({"error": "timed out after 120s"}, status_code=504)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {"app": APP_NAME, "status": "ok", **cli_status(), "python": platform.python_version()}
    )


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    st = cli_status()
    if st["cli_installed"]:
        status_html = f'<span class="ok">CLI installed · {st["cli_version"]}</span>'
    else:
        status_html = '<span class="warn">claude CLI not installed yet</span>'
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
    code {{ background: #0f1117; padding: .1rem .4rem; border-radius: 4px; color: #7dd3fc; }}
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
           font-size: .9rem; text-align: left; display: none; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>{APP_NAME}</code></h1>
    <div>Claude Code CLI · headless <code>claude -p</code> · scaffolder skills file</div>
    <div class="meta">{status_html}</div>
    <form onsubmit="run(event)">
      <div class="row">
        <input id="q" placeholder="give Claude Code a prompt…" aria-label="prompt">
        <button type="submit">run</button>
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
    async function run(e) {{
      e.preventDefault();
      const out = document.getElementById("out");
      out.style.display = "block"; out.textContent = "running (can take a minute)…";
      try {{
        const r = await fetch("/api/run", {{ method: "POST",
          headers: {{ "content-type": "application/json" }},
          body: JSON.stringify({{ prompt: document.getElementById("q").value,
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
