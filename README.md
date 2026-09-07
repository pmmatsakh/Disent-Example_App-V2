# Example App Library

A library of **30 self-contained "hello world" applications**, each demonstrating one
stack end-to-end: it builds, runs on its own port, is reverse-proxied by NGINX, and
renders as a live tile on a shared homepage.

Each app is deliberately minimal. The point isn't the app — it's proving the whole
path works: a language runs, a page renders, an endpoint answers, a database does
CRUD, an LLM completes, an agent loops.

## Architecture

```
Browser
  -> https://my-container-{port}.example.com
  -> wildcard DNS resolves to the platform
  -> platform routes BY PORT, encoded in the subdomain
  -> NGINX in the container proxies to the app on that port
  -> app (bound to 0.0.0.0:PORT) responds
```

Routing is **by port**, not by name — the app name never appears in the hostname.
Two consequences drive most of the code here:

- An app must bind `0.0.0.0`, never `127.0.0.1`. A loopback listener returns 502.
- Vite apps need `server.host: true` and an `allowedHosts` entry, or the dev server
  rejects the proxied Host header.

Apps run under **systemd** (not pm2) with `Restart=always`. The homepage is
data-driven: adding an app means editing `manifest.json`, not touching code.

## What's included

| Category | Apps |
|---|---|
| **Environments** | nodejs, python, go, c/c++ |
| **Frontend** | html/css/js, vite+react, tailwind, typescript |
| **Backend** | django, expressjs, fastapi, flask |
| **Fullstack** | nextjs, fastapi+react, fastapi+react+sqlite, django+react |
| **Databases** | postgres, mysql, redis, sqlite |
| **AI / agents** | langchain, crewai, autogen, n8n, mcp_server, claude_agent_sdk, openai_agent_sdk, claude_code, openai_codex |
| **Docs** | generated documentation site |

## Layout

```
{stack}-example/
  app/                 source
  app/nginx/*.conf     reverse-proxy config for this app's port
  app/.env.example     required env vars (placeholders only)
deploy-bundle/         deployable copies of every app
container-fixes/       manifest.json + homepage + deploy script
docs-example/          the documentation site
```

## Running one locally

```bash
cd nodejs-example/app
node app.js          # binds 0.0.0.0:8978
```

Python apps use `uv`:

```bash
cd fastapi-example/app
uv sync && uv run main.py
```

Apps needing API keys read them from a `.env` loaded via systemd's
`EnvironmentFile`. Copy `.env.example` to `.env` and fill it in — `.env` is
gitignored and no real key is ever committed.

## Notes

- Dependencies (`node_modules/`, `.venv/`) and build output are not committed;
  regenerate with `npm install` / `uv sync`.
- Hostnames and infrastructure identifiers in this repo are placeholders.
