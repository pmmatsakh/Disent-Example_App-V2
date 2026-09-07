# Deploy wave 1 — 11 apps  (2026-08-10)

No Node 22 required. The two Vite frontends are pre-built to static `dist/` and
served directly by nginx on their own port, so nothing needs a modern Node.

Deploying: fastapi 8000 · flask 8001 · django 3005 · expressjs 3006 ·
c_cpp 3007 · fastapi_react 8002 · fastapi_react_sqlite 8003 ·
django_react 8004 · tailwind 3003 · typescript 3004 · langchain 3401

---

## STEP 0 — Install uv on the container (once)

The box has **no pip at all** and `python3 -m venv` cannot build a usable env
(`ensurepip` missing), so the 8 Python apps need uv. It installs a single
binary to `~/.local/bin` — no apt, no system packages touched.

```bash
ssh my-container-host 'curl -LsSf https://astral.sh/uv/install.sh | sh'
ssh my-container-host '/root/.local/bin/uv --version'
```

**You should see:** a version like `uv 0.9.x`.
(deploy-all.sh finds uv even when it is not on the SSH PATH.)

## STEP 1 — Push the updated deploy.sh

It changed again since you pushed it: static apps can now listen on their own
port (they'd otherwise all collide on :80), and the bind check + direct-port
verification now cover static mode too.

```bash
cd ~/Desktop/sandbox/container-fixes
scp deploy.sh my-container-host:/root/projects/deploy/deploy.sh
ssh my-container-host 'chmod +x /root/projects/deploy/deploy.sh && echo OK'
```

## STEP 2 — Upload the bundle (~1 MB)

```bash
cd ~/Desktop/sandbox
scp -r deploy-bundle my-container-host:/root/projects/sandbox/
ssh my-container-host 'chmod +x /root/projects/sandbox/deploy-bundle/deploy-all.sh && echo OK'
```

## STEP 3 — Prove ONE app first (fastapi)

Don't bulk-deploy blind. This confirms the platform routes an arbitrary new
port, which nothing has tested yet.

```bash
ssh my-container-host '/root/projects/sandbox/deploy-bundle/deploy-all.sh fastapi'
```

**You should see:**
```
bind on :8000  ->  0.0.0.0:8000
OK: listening on all interfaces — reachable from the edge.
GET http://127.0.0.1:8000/ (direct — same path as the edge)  ->  HTTP 200
```

Then tell me — I'll check `https://my-container-8000.example.com/` in a
browser. **Stop here if it 502s**; that means the platform only routes certain
ports and the whole port plan needs Anthony.

## STEP 4 — Deploy the remaining 10

```bash
ssh my-container-host '/root/projects/sandbox/deploy-bundle/deploy-all.sh'
```

Already-deployed apps are simply redeployed — it's idempotent. The summary at
the end lists what succeeded and what failed.

## STEP 5 — Publish the tiles

Only after step 4 reports success (the manifest claims these are live):

```bash
cd ~/Desktop/sandbox/container-fixes
scp manifest.json my-container-host:/srv/apps/homepage/manifest.json
```

Then open **https://my-container-80.example.com/** — should show 15 live.

---

## Notes

- **langchain** works without any API key (bring-your-own-key in the UI). To
  also set a server key: `scp langchain-example/app/.env
  my-container-host:/srv/apps/langchain/.env`, add
  `EnvironmentFile=/srv/apps/langchain/.env` to the unit, restart. Never commit
  that file.
- **Not in this wave** (need Node 22): nextjs, n8n, openai_codex, claude_code.
- Rollback one app: `systemctl disable --now example-<name>` and
  `rm /etc/nginx/sites-enabled/<name>.conf && nginx -t && systemctl reload nginx`
