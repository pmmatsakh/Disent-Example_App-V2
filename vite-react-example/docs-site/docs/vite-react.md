# Running the `vite react` Example

A guide to running the Vite + React "hello world" — the *frontend* row from the
container spec, on port **5174**.

This one is **frontend-only**: there is no backend, no API, and no server-side
rendering. Vite serves the files, React runs entirely in your browser, and
`npm run build` produces plain static files that any web server can host.

!!! danger "Node.js 20.19+ (or 22.12+) is required"
    Current Vite (8.x) requires **Node.js 20.19+ or 22.12+**. The Disent
    container base image ships **Node 19**, which is too old — this app will not
    run there until the image is bumped to **Node 20 LTS or 22 LTS**. Check your
    version with `node --version` before you start.

## What's in the app

```
vite-app/
├── package.json          # dependencies (react, vite) + run scripts
├── vite.config.js        # Vite config — pins port 5174
├── index.html            # the entry document; React mounts into #root
├── src/
│   ├── main.jsx          # entry point — renders <App /> into the page
│   ├── App.jsx           # the component you see (a counter)
│   └── index.css         # styling
├── nginx/vite-react.conf # reverse-proxy config (deployment only)
└── homepage-tile.html    # container homepage tile (deployment only)
```

### How this differs from the other examples

- **`index.html` ships nearly empty.** It contains a single `<div id="root">`.
  Everything visible is drawn by React in the browser after the page loads.
- **There is no server code.** Compare with the *frontend/backend* Next.js row,
  which has an API route. Here, nothing runs on the server at all.
- **The build output is static.** `npm run build` writes a `dist/` folder of
  HTML, CSS, and JS. In production you can serve that folder from NGINX
  directly — no Node process required.

## Step 1 — Install dependencies

From inside the `vite-app/` folder:

```bash
npm install
```

This downloads Vite and React into `node_modules/`. One-time step.

## Step 2 — Run the dev server

```bash
npm run dev
```

Vite starts and prints a local URL. Open **http://localhost:5174**.

!!! tip "Try the hot reload"
    Click the counter a few times, then open `src/App.jsx`, change the heading
    text, and save. The page updates instantly **and the count stays where it
    was** — that's Hot Module Replacement, Vite's signature feature.

Stop the server with ++ctrl+c++.

## Step 3 — Verify it works

The page shows a "hello from vite react" card with a button. Click it — the
count goes up immediately, with no network request and no page reload. That
confirms React is mounted and running client-side.

## Step 4 — Production build (optional)

```bash
npm run build      # writes static files into dist/
npm run preview    # serves dist/ on 5174 to check the built output
```

Look inside `dist/` afterwards — it's just HTML, CSS, and JS. That's the whole
app; there's nothing else to deploy.

## Deployment files

- **`nginx/vite-react.conf`** — contains **two options**, documented inline:
    - **Option A** proxies to the Vite dev server on 5174 (matches the spec's
      port and keeps hot reload, but a dev process must stay running).
    - **Option B** serves the built `dist/` folder straight off disk with no
      Node process at all — the normal production shape for a frontend-only
      app. It includes the SPA fallback (`try_files … /index.html`) so client
      routes survive a refresh.

    Pick one and comment out the other.

- **`homepage-tile.html`** — the tile that lists this app on the container's
  example-app-browser homepage.

## Troubleshooting

??? failure "`You are using Node.js …` / Vite refuses to start"
    Your Node is too old. Vite 8 needs 20.19+ or 22.12+. Install Node 22 LTS
    (from [nodejs.org](https://nodejs.org), or `nvm install 22 && nvm use 22`),
    reopen the terminal, and re-run.

??? failure "`Port 5174 is already in use`"
    Something else holds the port — often an earlier copy of this server still
    running. Free it with `lsof -ti:5174 | xargs kill`, or run on another port:
    `npm run dev -- --port 5175`.

    The config sets `strictPort: true` on purpose: Vite will **fail loudly**
    rather than quietly moving to a different port. That matters because the
    NGINX proxy points at a fixed port — a silent switch would break it.

??? failure "Blank white page in the browser"
    React failed to mount. Open the browser's developer console (++cmd+option+i++
    on Mac) and look for an error. The usual causes are a typo in `src/App.jsx`
    or a missing `#root` div in `index.html`.

??? failure "`vite: command not found`"
    `npm install` didn't finish, or you're not in the `vite-app/` folder. Run
    `ls` — you should see `package.json` and `node_modules`. Re-run
    `npm install` if `node_modules` is missing.
