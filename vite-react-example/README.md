# vite-react-example

The *frontend* example from the container spec: a Vite + React "hello world"
that runs entirely in the browser. No backend, no server-side rendering — Vite
serves the files and React does the rest.

```
vite-react-example/
├── vite-app/       ← the runnable Vite + React app  (run this on port 5174)
│   ├── package.json, vite.config.js, index.html
│   ├── src/                      main.jsx, App.jsx, index.css
│   ├── nginx/vite-react.conf     (deployment only)
│   └── homepage-tile.html        (deployment only)
│
└── docs-site/      ← the MkDocs documentation site  (run this on port 8000)
    ├── mkdocs.yml, requirements.txt
    └── docs/index.md, docs/vite-react.md
```

`vite-app/` is the program. `docs-site/` is a website that *documents* how to
run it. They run separately, on different ports.

> **Node.js 20.19+ or 22.12+ is required.** Current Vite refuses to start on
> older Node. Your Mac is fine (Node 24). The container's Node 19 is **too old**
> and must be bumped to Node 20/22 LTS before this deploys there.

---

## Test 1 — the app (`vite-app/`)

```bash
cd vite-app
npm install        # one-time; downloads Vite + React
npm run dev
```

Open **http://localhost:5174**. You should see a "hello from vite react" card.
Click the button — the counter goes up instantly (React state, no server call).

Then try hot reload: with the page open, edit `src/App.jsx`, change the heading,
and save. The page updates immediately **and keeps your count**.

Stop it with **Ctrl + C**.

---

## Test 2 — the docs site (`docs-site/`)

```bash
cd docs-site
pip3 install -r requirements.txt      # one-time install
mkdocs serve
```

Open **http://localhost:8000**.

Stop it with **Ctrl + C**.

> **Port 8000 already in use?** An earlier `mkdocs serve` is probably still
> running from another example. Either free it —
> ```bash
> lsof -ti:8000 | xargs kill
> ```
> — or serve this one on a different port: `mkdocs serve -a localhost:8001`.

> If `pip3 install` fails with "externally-managed-environment", use a virtual
> environment:
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> mkdocs serve
> ```

---

The app (5174) and the docs (8000) use different ports, so you can run both at
once in two terminal windows.
