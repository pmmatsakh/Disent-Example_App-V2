# Running the `html_css_js` Example

A guide to running the plain HTML/CSS/JavaScript "hello world" — the *frontend*
row with no framework attached.

This is the simplest example in the whole library. There are **no
dependencies**, **no build step**, and **no `npm install`**. Three files, opened
by a browser, exactly as written.

!!! question "This row has no port assigned"
    The tracker leaves this row's port column blank (`tailwind` gets 3003,
    `typescript` gets 3004, but `html_css_js` is empty). The docs below use
    **3007** — the next free port in the 3000 block — but treat that as a
    **placeholder to confirm** with whoever owns the spec.

    It may well be deliberate: a static site needs no port at all in
    production, because NGINX serves the files straight off disk without any
    process running. The port only matters for local previewing.

!!! success "No Node.js version problem here"
    Unlike the `nextjs` and `vite react` rows — both of which are blocked by the
    container's Node 19 — this example has no runtime requirement at all. It
    will run on the container today, exactly as provisioned.

## What's in the app

```
static-app/
├── index.html            # STRUCTURE — what's on the page
├── styles.css            # APPEARANCE — how it looks
├── app.js                # BEHAVIOUR — what it does
├── nginx/html-css-js.conf  # NGINX config (deployment only)
└── homepage-tile.html      # container homepage tile (deployment only)
```

That's the entire app — about 5 KB total.

### The point of this example: three files, three jobs

The row's language column reads *"html, css, and javascript"* — three
languages, and the example keeps them cleanly separated:

- **`index.html`** describes *what exists*: a heading, some text, two buttons.
  It says nothing about colour or behaviour.
- **`styles.css`** decides *how it looks*. It's linked from the HTML and loaded
  by the browser unprocessed. (Compare the `tailwind` row, which adds a build
  step to *generate* CSS.)
- **`app.js`** makes it *do things*. It finds elements by `id` and attaches
  click handlers, talking to the DOM directly. (Compare the `vite react` row,
  where React manages the page for you and JSX gets compiled.)

The theme toggle shows the separation working: JavaScript doesn't set any
colours. It toggles a CSS *class* on `<body>`, and `styles.css` decides what
that class means.

## Step 1 — Serve the files

You can't just double-click `index.html`. Opening it as a `file://` path works
for this simple case, but browsers apply different security rules to local
files, so behaviour diverges from the real thing. Serve it over HTTP instead.

Python is already installed on macOS and in the container, so no install is
needed. From inside the `static-app/` folder:

```bash
python3 -m http.server 3007
```

=== "Prefer Node?"

    If you'd rather use Node, this works without installing anything
    permanently:

    ```bash
    npx serve -l 3007
    ```

=== "Why not just open the file?"

    Double-clicking `index.html` gives you a `file://` URL. It'll mostly work
    here, but `file://` blocks `fetch`, module imports, and other features
    you'd want as soon as the example grows. Serving over HTTP matches how the
    page actually runs in the container.

## Step 2 — Open it

Go to **http://localhost:3007**.

You'll see the "hello from html_css_js" card. Verify all three files are doing
their job:

1. **HTML** — the card, heading, and buttons are there.
2. **CSS** — it's styled (dark card, rounded corners, blue accent). If you see
   unstyled black-on-white text, `styles.css` didn't load.
3. **JavaScript** — click the button and the count goes up; click *"switch
   accent colour"* and the blue turns pink. The bottom line shows the time the
   page ran in your browser.

If all three work, the example is complete.

Stop the server with ++ctrl+c++.

## Step 3 — Try editing it

There's no build step, so the loop is immediate: edit a file, save, refresh the
browser. No compiling, no restarting the server.

Try changing `--accent` in `styles.css` from `#7dd3fc` to any colour and
refreshing.

!!! note "No hot reload"
    Unlike the `vite react` row, you must refresh the page manually. Hot reload
    is a feature of build tools — and this example deliberately has none. That
    trade-off *is* the lesson: zero tooling means zero setup, but also zero
    conveniences.

## Deployment files

- **`nginx/html-css-js.conf`** — this row's config is unlike all the others. It
  uses `root`, **not `proxy_pass`**, because there's no application to proxy
  *to*. NGINX reads the three files off disk and sends them to the browser.
  There's no process to keep alive — no `pm2`, no `systemd` unit.

    It also sets cache headers: assets cached for an hour, HTML never cached.
    Frameworks solve staleness by hashing filenames on build; with
    hand-written files, the server has to say so explicitly.

- **`homepage-tile.html`** — the tile that lists this app on the container's
  example-app-browser homepage.

## Troubleshooting

??? failure "The page loads but looks unstyled (plain text on white)"
    `styles.css` didn't load. Check that it sits in the *same folder* as
    `index.html`, and that the filename matches exactly — `styles.css`, not
    `style.css`. Open the browser's Network tab and look for a 404.

??? failure "The buttons don't do anything"
    `app.js` didn't load or hit an error. Open the browser console
    (++cmd+option+i++ on Mac) and look for a red error. The usual cause is a
    filename mismatch or a typo in the JavaScript — and since nothing compiles
    this file, a typo only surfaces at runtime, in the console.

??? failure "`Address already in use` on port 3007"
    Something else holds the port. Free it with `lsof -ti:3007 | xargs kill`, or
    just pick another: `python3 -m http.server 3008`.

??? failure "`python3: command not found`"
    Rare on macOS, but install Python from [python.org](https://python.org) if
    so — or use the Node alternative: `npx serve -l 3007`.
