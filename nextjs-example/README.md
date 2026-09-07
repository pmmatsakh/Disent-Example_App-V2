# nextjs-example

The *frontend/backend* example from the container spec: a Next.js "hello world"
that serves both a server-rendered page and a backend API route. Two things live
in this folder, kept separate on purpose:

```
nextjs-example/
├── nextjs-app/     ← the runnable Next.js app  (run this on port 3000)
│   ├── package.json, next.config.js
│   ├── app/                    the page, the API route, styling
│   ├── nginx/nextjs.conf       (deployment only)
│   └── homepage-tile.html      (deployment only)
│
└── docs-site/      ← the MkDocs documentation site  (run this on port 8000)
    ├── mkdocs.yml, requirements.txt
    └── docs/index.md, docs/nextjs.md
```

`nextjs-app/` is the program. `docs-site/` is a website that *documents* how to
run it. They run separately, on different ports.

> **Node.js 20.9+ is required.** Current Next.js refuses to start on older Node.
> Your Mac is fine (Node 24). The container's Node 19 is **too old** and must be
> bumped to Node 20/22 LTS before this deploys there.

---

## Test 1 — the app (`nextjs-app/`)

```bash
cd nextjs-app
npm install        # one-time; downloads Next.js + React
npm run dev
```

Open **http://localhost:3000**. You should see a "hello from nextjs" card.
Click **"call the backend →"** — it fetches the `/api/hello` route and shows the
JSON response. You can also open **http://localhost:3000/api/hello** directly.

Stop it with **Ctrl + C**.

---

## Test 2 — the docs site (`docs-site/`)

```bash
cd docs-site
pip3 install -r requirements.txt      # one-time install
mkdocs serve
```

Open **http://localhost:8000** — the documentation site loads with the nextjs
guide in the navigation.

Stop it with **Ctrl + C**.

> If `pip3 install` fails with "externally-managed-environment", use a virtual
> environment instead:
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> mkdocs serve
> ```

---

The app (3000) and the docs (8000) use different ports, so you can run both at
once in two terminal windows.
