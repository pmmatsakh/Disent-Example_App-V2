# nodejs-example

Two things live in this folder, kept separate on purpose:

```
nodejs-example/
├── app/            ← the runnable Node app  (run this on port 8978)
│   ├── server.js
│   ├── package.json
│   ├── nginx/nodejs.conf     (deployment only — not needed to run locally)
│   └── homepage-tile.html    (deployment only — not needed to run locally)
│
└── docs-site/      ← the MkDocs documentation site  (run this on port 8000)
    ├── mkdocs.yml
    ├── requirements.txt
    └── docs/
        ├── index.md
        └── nodejs.md          ← the manual that explains how to run the app
```

**The two are independent.** `app/` is the actual program. `docs-site/` is a
website that *documents* how to run that program. They run separately, on
different ports, and never talk to each other.

---

## Test 1 — the app (`app/`)

```bash
cd app
npm start
```

You'll see `[nodejs] listening on http://127.0.0.1:8978`. Open
**http://127.0.0.1:8978** in a browser — you should see a "hello from nodejs"
card. Check **http://127.0.0.1:8978/health** too; it returns JSON.

Stop it with **Ctrl + C**. (No `npm install` needed — the app has no
dependencies.)

---

## Test 2 — the docs site (`docs-site/`)

```bash
cd docs-site
pip3 install -r requirements.txt      # one-time install
mkdocs serve
```

You'll see a line ending in `Serving on http://127.0.0.1:8000/`. Open
**http://127.0.0.1:8000** — the documentation site loads, with the nodejs guide
in the navigation.

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

You can run both at once in two separate terminal windows — the app on 8978 and
the docs on 8000 don't collide.
