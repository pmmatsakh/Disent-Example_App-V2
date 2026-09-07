# Building the `nodejs` Example

A step-by-step guide to recreating the vanilla Node.js "hello world" example on
any machine, starting from nothing. Follow it top to bottom and you'll end up
with a running server serving the hello-world page on port **8978**.

This is the simplest app in the container's library — an *environments* row: a
bare language sandbox with no framework.

## What you'll end up with

A folder containing four files:

| File | Purpose |
|------|---------|
| `server.js` | The Node server. Listens on port 8978, serves an HTML page at `/` and JSON at `/health`. |
| `package.json` | Lets you run the app with `npm start`. |
| `nginx/nodejs.conf` | Reverse-proxy config (only needed when deploying to the container). |
| `homepage-tile.html` | The tile that lists this app on the container's homepage (deployment only). |

!!! note
    Only `server.js` and `package.json` are needed to run the app locally. The
    other two files are for the container deployment phase.

## Prerequisites

You need **Node.js 18 or newer**. The Disent container ships Node 19; any modern
version works, since the code uses only Node's standard library.

Check whether you already have it:

```bash
node --version
```

=== "Already installed"

    If you see `v20.x` or higher, you're set — continue to Step 1.

=== "Not installed"

    If you see `command not found`, download the **LTS** installer from
    [nodejs.org](https://nodejs.org), run it, then **close and reopen your
    terminal** so it picks up the new command. Re-run `node --version` to
    confirm.

## Step 1 — Create the project folder

Pick a place for the project and create a folder for it — for example, on the
Desktop:

```bash
mkdir -p ~/Desktop/nodejs
cd ~/Desktop/nodejs
```

The `cd` puts you *inside* the folder; everything from here happens in this
directory. Confirm where you are:

```bash
pwd
```

It should print a path ending in `/nodejs`.

## Step 2 — Create `server.js`

This is the whole application. Create it in your editor, or straight from the
terminal with the here-doc below — copy the entire block and paste it in one go:

```bash title="Create server.js"
cat > server.js << 'EOF'
// nodejs environment example — vanilla Node, no framework.
// (Express lives in its own row; this one deliberately uses only the stdlib.)
//
// Binds TCP 8978 on 127.0.0.1. NGINX terminates 80/443 on the public
// subdomain and reverse-proxies here — see nginx/nodejs.conf.

import http from "node:http";
import os from "node:os";

const PORT = process.env.PORT || 8978;
const HOST = process.env.HOST || "127.0.0.1";
const APP_NAME = "nodejs";

const page = () => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${APP_NAME} — hello world</title>
  <style>
    body { font: 16px/1.5 system-ui, sans-serif; margin: 0;
           display: grid; place-items: center; min-height: 100vh;
           background: #0f1117; color: #e6e8ee; }
    .card { text-align: center; padding: 2rem 2.5rem; border: 1px solid #262b38;
            border-radius: 12px; background: #161a23; }
    h1 { margin: 0 0 .25rem; font-size: 1.4rem; }
    code { background: #0f1117; padding: .1rem .4rem; border-radius: 4px;
           color: #7dd3fc; }
    .meta { color: #8a93a6; font-size: .85rem; margin-top: 1rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>👋 hello from <code>${APP_NAME}</code></h1>
    <div>vanilla Node.js · no framework</div>
    <div class="meta">
      served by ${os.hostname()} · node ${process.version}<br>
      listening on ${HOST}:${PORT} · <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>`;

const server = http.createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ app: APP_NAME, status: "ok", node: process.version }));
    return;
  }
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  res.end(page());
});

server.listen(PORT, HOST, () => {
  console.log(`[${APP_NAME}] listening on http://${HOST}:${PORT}`);
});
EOF
```

What this code does:

- Reads `PORT` (default **8978**) and `HOST` (default `127.0.0.1`) from
  environment variables, so you can override them without editing the file.
- Binds to `127.0.0.1` on purpose — in the container, NGINX is the only thing
  that should reach the app directly.
- Handles two routes: `/health` returns a small JSON status object; everything
  else returns the HTML hello-world page.
- Uses only `node:http` and `node:os`, both built into Node — so there are **no
  dependencies to install**.

## Step 3 — Create `package.json`

This tells `npm` how to start the app.

```bash title="Create package.json"
cat > package.json << 'EOF'
{
  "name": "nodejs",
  "version": "1.0.0",
  "description": "Vanilla Node.js hello-world example (environments category)",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  }
}
EOF
```

Two fields matter most:

- `"type": "module"` enables the modern `import` syntax used in `server.js`.
- `"scripts.start"` makes `npm start` run `node server.js`.

## Step 4 — Run it

From inside the folder:

```bash
npm start
```

You should see:

```
> nodejs@1.0.0 start
> node server.js

[nodejs] listening on http://127.0.0.1:8978
```

!!! tip
    Leave this terminal window open — the server runs until you stop it. There's
    no `npm install` step because the app has no dependencies.

## Step 5 — Verify it works

Open a browser and go to:

```
http://127.0.0.1:8978
```

You'll see a dark card reading **"👋 hello from nodejs"** with your machine name
and Node version. Then check the second route:

```
http://127.0.0.1:8978/health
```

This returns JSON like `{"app":"nodejs","status":"ok","node":"v20.x.x"}`. If both
load, the example is working end-to-end.

## Step 6 — Stop it

In the terminal running the server, press ++ctrl+c++. The server shuts down.
Closing the terminal window stops it too.

## Deployment files

When this example goes into the Disent container, two more files come into play.
They aren't needed to run locally, but here they are for completeness.

### `nginx/nodejs.conf`

Routes a public subdomain to the app's local port.

```bash title="Create nginx/nodejs.conf"
mkdir -p nginx
cat > nginx/nodejs.conf << 'EOF'
# NGINX reverse proxy for the `nodejs` example.
# Drop into the container's sites-enabled and reload:
#   sudo cp nodejs.conf /etc/nginx/sites-enabled/nodejs.conf
#   sudo nginx -t && sudo systemctl reload nginx
#
# Routing is BY PORT (CLAUDE.md §2): my-container-8978.example.com maps to
# container:8978. A per-app server_name is unnecessary, and deploy.sh
# regenerates this conf on every run — so server_name _ (catch-all) is fine.
# TLS on 443 is handled by the container's existing cert setup (Certbot/wildcard).

server {
    listen 80;
    listen [::]:80;
    server_name _;

    location / {
        proxy_pass         http://127.0.0.1:8978;
        proxy_http_version 1.1;

        # Standard forwarded headers
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket upgrade support — harmless here, but keep it in the
        # template so the same block works for the fullstack/AI rows later.
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
```

### `homepage-tile.html`

The tile that surfaces this app on the container's example-app-browser homepage.

```bash title="Create homepage-tile.html"
cat > homepage-tile.html << 'EOF'
<!-- Homepage entry for the "example app browser / default home page".
     The landing page iframes each sub-app on its subdomain. Add one
     block like this per example. URL is port-routed:
     my-container-{port}.example.com  (CLAUDE.md §2 — NOT the retired
     *.fastcontainers.net scheme, which is a bug per §4). -->

<article class="app-tile" data-category="environments" data-lang="javascript">
  <header>
    <h3>nodejs</h3>
    <span class="badge">environments · javascript · :8978</span>
  </header>

  <!-- live preview of the running app -->
  <iframe
    src="https://my-container-8978.example.com"
    title="nodejs hello world"
    loading="lazy"
    style="width:100%; height:220px; border:0; border-radius:8px;"></iframe>

  <footer>
    <a href="https://my-container-8978.example.com" target="_blank" rel="noopener">
      open example ↗
    </a>
    <a href="https://git.example.com/philip/nodejs" target="_blank" rel="noopener">
      source
    </a>
  </footer>
</article>
EOF
```

Deploying to the container is then three actions: keep the app running (with
`pm2` or a `systemd` unit so it survives reboots), copy the NGINX config into
`sites-enabled` and reload NGINX, and add the homepage tile to the landing page.

## Troubleshooting

??? failure "`cd: no such file or directory`"
    The path is wrong or has a stray space. `cd ~ /Desktop/nodejs` (with a space
    after `~`) is read as two arguments and fails — write it as one path:
    `cd ~/Desktop/nodejs`.

??? failure "`permission denied` when you type a path"
    You typed a folder path on its own line with no command in front of it. A
    bare path makes the shell try to *execute* the folder. Put `cd` in front:
    `cd /full/path/to/folder`.

??? failure "`zsh: command not found: npm`"
    Node isn't installed, or the terminal predates the install. Install the LTS
    build from [nodejs.org](https://nodejs.org), then close and reopen the
    terminal.

??? failure "`Cannot find module ... server.js`"
    You're not in the folder that contains `server.js`. Run `ls` — you should
    see `server.js` and `package.json`. If they're one level deeper, `cd` into
    that subfolder.

??? failure "`EADDRINUSE` (address already in use)"
    Port 8978 is taken, maybe by an earlier copy still running. Stop the old one
    with ++ctrl+c++, or start this one on a different port: `PORT=8979 npm start`.
