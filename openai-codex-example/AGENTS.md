# Disent Tile Scaffolder (Codex AGENTS.md)

Project instructions for OpenAI Codex. Same scaffolder contract as
claude-code-example/SKILL.md — kept in sync; the corpus conventions below are
identical for every AI agent building Disent tiles.
# Disent Tile Scaffolder

You are scaffolding a new "hello world" tile for the Disent dev-container
platform. The verified corpus of ~14 existing examples in this repository is
your reference — **always clone the nearest existing example rather than
inventing structure.**

## Platform facts (non-negotiable)

1. **Routing is BY PORT.** The public URL is
   `https://my-container-{port}.example.com` → `container:{port}`.
   Never use any other scheme (`*.fastcontainers.net` is retired — it is a bug).
2. **Bind `0.0.0.0`, never `127.0.0.1`.** Default it in code
   (`HOST = os.environ.get("HOST", "0.0.0.0")`) — do not rely on env overrides.
3. **Vite apps** need `server: { host: true, allowedHosts: ['.example.com'] }`.
   Django needs `ALLOWED_HOSTS` permitting the edge host.
4. **nginx conf** uses `server_name _;` (catch-all) — deploy.sh regenerates the
   real conf, so the file is documentation of the proxy target port.
5. **Secrets** go in a git-ignored `.env` loaded via systemd `EnvironmentFile`.
   Never hard-code, never commit. Ship a `.env.example`.
6. **systemd, not pm2.** Pin an explicit supported Node executable in
   `ExecStart`; on the current container `/usr/bin/node` is the retired Node 18
   binary, while Node 22.22.2 is under `/root/.nvm/versions/node/`.
7. Serve from `/srv/apps/{name}/`, `chown www-data` — never `/root`.

## Required folder shape

```
{name}-example/
├── app/  (or backend/ + frontend/ for fullstack)
│   ├── <entrypoint>            # binds 0.0.0.0:{port}; "/" HTML card + /health JSON
│   ├── <deps file>             # requirements.txt or package.json
│   ├── nginx/{name}.conf       # proxy_pass to 127.0.0.1:{port}, server_name _
│   └── homepage-tile.html      # iframe of the port-routed URL
```

## Which corpus example to clone

| New tile is a…           | Clone from                      |
|--------------------------|---------------------------------|
| bare runtime             | `nodejs-example` / `c-cpp-example` |
| Python backend           | `fastapi-example` (or `flask`/`django`) |
| Node backend             | `expressjs-example`             |
| frontend (Vite)          | `tailwind-example` / `typescript-example` |
| fullstack (one port)     | `fastapi-react-example` (backend serves built React + /api, no CORS) |
| fullstack + persistence  | `fastapi-react-sqlite-example`  |
| AI/CLI framework         | `langchain-example` (thin FastAPI wrapper, graceful no-key state) |

## Visual identity (all tiles match)

Dark card: bg `#0f1117`, card `#161a23`, border `#262b38`, accent `#7dd3fc`,
muted `#8a93a6`. Title: `👋 hello from <code>{name}</code>`. Include a runtime
version line and a `/health` link.

## Port assignment

Ports come from the tracker spreadsheet — **never invent one**. If the row has
no port, mark every reference `PROPOSED — confirm with Anthony` and pick the
next free number in the row's category block (frontend/backend 300x,
fullstack 800x, AI 340x).

## Definition of done

1. App runs locally, renders in a real browser, `/health` returns JSON.
2. Bind check shows `*:{port}` (0.0.0.0), not `127.0.0.1`.
3. All four files present; URLs use the correct port-routed scheme.
4. AI tiles: work WITHOUT a key (honest degraded state + `key_present` in
   /health); keys only via `.env`.
5. "Done" ultimately means rendering through the real edge
   (`my-container-{port}.example.com`) — localhost passing is a draft.
