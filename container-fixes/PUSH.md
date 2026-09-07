# Container fixes — step by step (2026-08-10)

Four patched files, all validated locally. Container writes are gated by the
harness, so you run these. Every step is reversible and backed up first.

Run each STEP as one block, check the "you should see" line, then continue.

---

## STEP 1 — Back up the four originals

```bash
ssh my-container-host '
  cp /srv/apps/homepage/manifest.json   /root/manifest.json.bak
  cp /srv/apps/homepage/app.js          /root/app.js.bak
  cp /root/projects/deploy/deploy.sh    /root/deploy.sh.bak
  cp /etc/nginx/sites-available/default /root/nginx-default.bak
  ls -1 /root/*.bak'
```

**You should see:** four `.bak` files listed.

---

## STEP 2 — Push the four patched files

Note: `sites-enabled/default` is a symlink, so the real file is in
`sites-available/`. That is the correct target.

```bash
cd ~/Desktop/sandbox/container-fixes

scp manifest.json      my-container-host:/srv/apps/homepage/manifest.json
scp app.js             my-container-host:/srv/apps/homepage/app.js
scp deploy.sh          my-container-host:/root/projects/deploy/deploy.sh
scp nginx-default.conf my-container-host:/etc/nginx/sites-available/default

ssh my-container-host 'chmod +x /root/projects/deploy/deploy.sh && echo PUSHED'
```

**You should see:** four transfers, then `PUSHED`.

---

## STEP 3 — Reload nginx  (this fixes the homepage 502 on :80)

`nginx -t` validates first; if it fails, nothing reloads.

```bash
ssh my-container-host 'nginx -t && systemctl reload nginx && echo RELOADED'
```

**You should see:** `syntax is ok`, `test is successful`, then `RELOADED`.

**If it fails**, restore and tell me:
```bash
ssh my-container-host '
  cp /root/nginx-default.bak /etc/nginx/sites-available/default
  nginx -t && systemctl reload nginx && echo RESTORED'
```

---

## STEP 4 — Dry-run the nodejs redeploy  (changes nothing yet)

```bash
ssh my-container-host '/root/projects/deploy/deploy.sh \
  --name nodejs --mode proxy --port 8978 \
  --dir /srv/apps/nodejs --exec "/root/.nvm/versions/node/v22.22.2/bin/node server.js" --dry-run'
```

**You should see:** `host: my-container-8978.example.com` (port-based, not
`philip-nodejs.fastcontainers.net`), and a unit containing
`Environment=HOST=0.0.0.0`.

---

## STEP 5 — Run it for real  (this fixes the :8978 502)

Same command, without `--dry-run`:

```bash
ssh my-container-host '/root/projects/deploy/deploy.sh \
  --name nodejs --mode proxy --port 8978 \
  --dir /srv/apps/nodejs --exec "/root/.nvm/versions/node/v22.22.2/bin/node server.js"'
```

**You should see:**
```
bind on :8978  ->  0.0.0.0:8978
OK: listening on all interfaces — reachable from the edge.
GET http://my-container-8978.example.com/ (via nginx)  ->  HTTP 200
```
The bind line is the one that matters — it was `127.0.0.1:8978`.

---

## STEP 6 — Tell me "pushed"

I'll re-test both edge URLs that currently return 502:

  https://my-container-8978.example.com/
  https://my-container-80.example.com/

---

## Full rollback (if anything looks wrong)

```bash
ssh my-container-host '
  cp /root/manifest.json.bak /srv/apps/homepage/manifest.json
  cp /root/app.js.bak        /srv/apps/homepage/app.js
  cp /root/deploy.sh.bak     /root/projects/deploy/deploy.sh
  cp /root/nginx-default.bak /etc/nginx/sites-available/default
  nginx -t && systemctl reload nginx && echo ROLLED_BACK'
```
