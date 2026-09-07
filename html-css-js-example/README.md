# html-css-js-example

The *frontend* row with no framework: a hello world in plain HTML, CSS, and
JavaScript. **No dependencies, no build step, no `npm install`** — three files
a browser opens exactly as written. It's the simplest example in the library.

```
html-css-js-example/
├── static-app/     ← the app  (preview on port 3007)
│   ├── index.html              STRUCTURE — what's on the page
│   ├── styles.css              APPEARANCE — how it looks
│   ├── app.js                  BEHAVIOUR — what it does
│   ├── nginx/html-css-js.conf  (deployment only)
│   └── homepage-tile.html      (deployment only)
│
└── docs-site/      ← the MkDocs documentation site  (run on port 8000)
    ├── mkdocs.yml, requirements.txt
    └── docs/index.md, docs/html-css-js.md
```

> **Two things to know before you start**
>
> **No Node version problem here.** Unlike the `nextjs` and `vite react` rows —
> both blocked by the container's Node 19 — this example has no runtime
> requirement at all. It runs on the container as provisioned today.
>
> **The port is a placeholder.** The tracker leaves this row's port blank. These
> files use **3007** (next free in the 3000 block) — confirm with whoever owns
> the spec. A static site needs no port in production anyway; NGINX serves the
> files off disk.

---

## Test 1 — the app (`static-app/`)

There's nothing to install. Just serve the folder:

```bash
cd static-app
python3 -m http.server 3007
```

Open **http://localhost:3007**. Check all three files are working:

- **HTML** — the card and buttons are there.
- **CSS** — it's styled (dark card, blue accent). Unstyled text means
  `styles.css` didn't load.
- **JS** — click the button (count goes up), click *"switch accent colour"*
  (blue turns pink).

Stop it with **Ctrl + C**.

*Prefer Node? `npx serve -l 3007` works too.*

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
> — or serve this one elsewhere: `mkdocs serve -a localhost:8001`.

---

The app (3007) and the docs (8000) use different ports, so both can run at once.
