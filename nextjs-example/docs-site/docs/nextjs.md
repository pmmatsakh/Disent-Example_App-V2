# Running the `nextjs` Example

A guide to running the Next.js "hello world" — the *frontend/backend* row from
the container spec. Unlike the bare-Node example, this is a real framework: it
has dependencies (so there's an install step) and it demonstrates both halves of
a web app in one project — a server-rendered page **and** a backend API route,
on port **3000**.

!!! danger "Node.js 20.9 or newer is required"
    Current Next.js (16.x) **refuses to start on Node.js older than 20.9**. The
    Disent container base image ships **Node 19**, which is too old — the app
    will not run there until the image is bumped to **Node 20 LTS or 22 LTS**.
    This is a provisioning change to raise with whoever builds the container.
    Check your version with `node --version` before you start.

## What's in the app

```
nextjs-app/
├── package.json          # dependencies (next, react) + run scripts
├── next.config.js        # minimal Next.js config
├── app/                  # the App Router — Next owns this folder
│   ├── layout.jsx        # root layout (required; wraps every page)
│   ├── page.jsx          # the home page — a Server Component (frontend)
│   ├── Ping.jsx          # a Client Component: button that calls the API
│   ├── globals.css       # styling
│   └── api/hello/route.js  # the backend API route (/api/hello)
├── nginx/nextjs.conf     # reverse-proxy config (deployment only)
└── homepage-tile.html    # container homepage tile (deployment only)
```

### How the "frontend/backend" pieces fit together

- **`app/page.jsx`** is a *Server Component* — Next.js renders it to HTML on the
  server. This is the **frontend**.
- **`app/api/hello/route.js`** is a *Route Handler* — it runs only on the server
  and answers requests at `/api/hello`, returning JSON. This is the **backend**.
- **`app/Ping.jsx`** is a *Client Component* (marked `"use client"`) — it runs
  in the browser, and its button `fetch`es `/api/hello` and shows the response.
  That click is the frontend calling the backend, all inside one app.

## Step 1 — Install dependencies

From inside the `nextjs-app/` folder:

```bash
npm install
```

This downloads Next.js and React into a `node_modules/` folder. It's a one-time
step (repeat only when dependencies change).

## Step 2 — Run the dev server

```bash
npm run dev
```

You'll see Next.js start and print a local URL. Open **http://localhost:3000**.

!!! tip
    `npm run dev` enables hot reload — save any file and the browser updates
    automatically. Leave the terminal running while you work; stop it with
    ++ctrl+c++.

## Step 3 — Verify both halves work

1. **Frontend** — the page at `http://localhost:3000` shows a "hello from
   nextjs" card. That HTML was rendered by Next.js on the server.
2. **Backend** — click **"call the backend →"**. The button fetches
   `/api/hello` and displays the JSON it returns. You can also open
   **http://localhost:3000/api/hello** directly in the browser to see the raw
   response.

If the card loads *and* the button shows JSON, the full frontend → backend loop
is working.

## Step 4 — Production build (optional)

The dev server is for development. To see how it runs in production:

```bash
npm run build      # compiles an optimized build
npm start          # serves it on port 3000
```

This is the mode you'd use inside the container (kept alive by `pm2` or a
`systemd` unit).

## Deployment files

Two files matter only when deploying into the container:

- **`nginx/nextjs.conf`** — proxies the port-routed edge
  (`my-container-3000.example.com`, CLAUDE.md §2) to `127.0.0.1:3000`. It
  includes WebSocket-upgrade headers, which Next.js needs for hot reload to work
  through the proxy.
- **`homepage-tile.html`** — the tile that lists this app on the container's
  example-app-browser homepage.

Deploying is then: install and build the app, keep it running (`pm2`/`systemd`),
copy the NGINX config into `sites-enabled` and reload NGINX, and add the
homepage tile to the landing page.

## Troubleshooting

??? failure "`You are using Node.js 18.x` / `Node.js version >= v20.9.0 is required`"
    Your Node is too old for Next.js 16. Install Node 20 LTS or 22 LTS (via the
    installer at [nodejs.org](https://nodejs.org), or `nvm install 22 && nvm use
    22`), reopen the terminal, and re-run.

??? failure "`next: command not found` after install"
    Either `npm install` didn't finish, or you're not in the `nextjs-app/`
    folder. Run `ls` — you should see `package.json` and a `node_modules`
    folder. Re-run `npm install` if `node_modules` is missing.

??? failure "Port 3000 is already in use (`EADDRINUSE`)"
    Something else is on 3000 (maybe an earlier copy). Stop it with ++ctrl+c++,
    or run on another port: `npm run dev -- -p 3001`.

??? failure "The button shows an error instead of JSON"
    The API route didn't respond. Confirm `app/api/hello/route.js` exists and
    that the dev server is still running in its terminal (no crash messages).
