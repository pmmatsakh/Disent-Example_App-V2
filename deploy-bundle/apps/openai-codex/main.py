# openai_codex AI example — OpenAI's Codex CLI behind a thin web tile.
#
# The capability this tile proves: the Codex CLI is installed (locally, in this
# example's node_modules) and can run a prompt headlessly (`codex exec`), which
# is the foundation the "skills file" scaffolder row builds on — see AGENTS.md
# next to this app (Codex's convention for project instructions, the analogue
# of claude_code's SKILL.md).
#
# Auth: OPENAI_API_KEY from .env (systemd EnvironmentFile on the container,
# CLAUDE.md §8) or `codex auth`. With neither, the tile renders and reports
# status honestly.
#
# Binds 0.0.0.0:3403 (§8). my-container-3403.example.com -> :3403.
# NOTE: :3403 is a PROPOSED port (AI 3400s block) — confirm with Anthony.

import os
import platform
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

APP_NAME = "openai_codex"
PORT = int(os.environ.get("PORT", 3403))
HOST = os.environ.get("HOST", "0.0.0.0")  # bind all interfaces — required (§8)

# Local install: ../node_modules/.bin/codex (falls back to PATH).
LOCAL_CODEX = (Path(__file__).parent.parent / "node_modules" / ".bin" / "codex").resolve()

app = FastAPI(title=f"{APP_NAME} — AI hello world")


NVM_BIN = "/root/.nvm/versions/node/v22.22.2/bin"


def codex_bin() -> str | None:
    """Local install first, then the nvm Node 22 prefix, then PATH.

    systemd's PATH has neither the local node_modules nor nvm, and
    /usr/bin/node is the old Node 18 that codex refuses to run on.
    """
    if LOCAL_CODEX.is_file():
        return str(LOCAL_CODEX)
    cand = os.path.join(NVM_BIN, "codex")
    if os.path.isfile(cand) and os.access(cand, os.X_OK):
        return cand
    import shutil

    return shutil.which("codex")


def cli_status() -> dict:
    binpath = codex_bin()
    version = None
    if binpath:
        try:
            version = subprocess.run(
                [binpath, "--version"], capture_output=True, text=True, timeout=15
            ).stdout.strip()
        except Exception:
            version = "installed (version check failed)"
    return {
        "cli_installed": bool(binpath),
        "cli_version": version,
        "key_present": bool(os.environ.get("OPENAI_API_KEY")),
    }


class Ask(BaseModel):
    prompt: str
    api_key: str | None = None  # BYOK — per-request, never persisted


@app.post("/api/run")
def run(body: Ask) -> JSONResponse:
    st = cli_status()
    if not st["cli_installed"]:
        return JSONResponse(
            {"error": "codex CLI not installed. `npm install @openai/codex`"},
            status_code=503,
        )
    user_key = (body.api_key or "").strip()
    if not user_key and not st["key_present"]:
        return JSONResponse(
            {"error": "No API key: paste yours in the key field (used per-request, "
                      "never stored), or set OPENAI_API_KEY in .env."},
            status_code=503,
        )
    p = body.prompt.strip()
    if not p:
        return JSONResponse({"error": "prompt is required"}, status_code=400)
    # BYOK: a request-supplied key is injected into THIS subprocess's env only —
    # never stored, logged, or exported to the server process.
    env = os.environ.copy()
    if user_key:
        env["OPENAI_API_KEY"] = user_key
    try:
        # `codex exec` = headless, non-interactive mode. 120s guard.
        #  --skip-git-repo-check: codex refuses to run outside a trusted git
        #     repo without this, and the example folders are not git repos.
        #  stdin=DEVNULL: without it codex waits on stdin ("Reading additional
        #     input from stdin...") and hangs until the timeout.
        out = subprocess.run(
            [codex_bin(), "exec", "--skip-git-repo-check", p],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            stdin=subprocess.DEVNULL,
        )
        if out.returncode != 0:
            return JSONResponse(
                {"error": out.stderr.strip() or "codex exited nonzero"}, status_code=502
            )
        return JSONResponse({"answer": out.stdout.strip()})
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
    bits = []
    bits.append(
        f'<span class="ok">CLI installed · {st["cli_version"]}</span>'
        if st["cli_installed"]
        else '<span class="warn">codex CLI not installed yet</span>'
    )
    bits.append(
        '<span class="ok">key configured</span>'
        if st["key_present"]
        else '<span class="warn">no OPENAI_API_KEY yet</span>'
    )
    status_html = " · ".join(bits)
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
    <div>OpenAI Codex CLI · headless <code>codex exec</code> · scaffolder skills file</div>
    <div class="meta">{status_html}</div>
    <form onsubmit="run(event)">
      <div class="row">
        <input id="q" placeholder="give Codex a prompt…" aria-label="prompt">
        <button type="submit">run</button>
      </div>
      <div class="row">
        <input id="key" type="password" autocomplete="off"
               placeholder="your OpenAI API key (optional — per-request, never stored)"
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
