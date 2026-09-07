// Renders the example-app browser from manifest.json.
//
// Two deliberate design choices:
//
// 1. NOTHING IS HARD-CODED. Every tile comes from manifest.json. Adding an app
//    is a data edit, not a code edit — which matters when the tracker has ~35
//    rows and they land over time.
//
// 2. IFRAMES ARE NOT AUTO-LOADED. The tiles point at
//    {project}-{app}.{domain} subdomains. Those only resolve once DNS is
//    configured, and nothing on this container configures it yet. Auto-loading
//    35 iframes against unresolvable names would render a wall of browser error
//    pages. Instead each tile loads its preview on demand, and we probe first
//    so the page can say plainly whether routing works.

const STATUS_ORDER = { live: 0, todo: 1, blocked: 2, "needs-scoping": 3 };
const CATEGORY_ORDER = [
  "docs",
  "environments",
  "frontend",
  "frontend/backend",
  "backend",
  "databases",
  "fullstack",
  "ai",
];

let MANIFEST = null;
let DNS_OK = false;
let activeFilter = "all";

// Build a sibling app's URL.
//
// Scheme and port are inherited from wherever THIS page is being served, not
// hard-coded. The sibling apps sit behind the same nginx, so if you reached the
// homepage over an SSH tunnel on :8080, the other apps are on :8080 too. Hard
// -coding port 80 would break every preview when tunnelling — which is the
// normal case until DNS exists.
//
// Routing is BY PORT (verified live 2026-08-10): the platform maps
// {project}-{PORT}.{domain} straight through to container:{PORT}. The app NAME
// never appears in the hostname — e.g. https://my-container-8978.example.com
// Static apps have no port of their own; nginx serves them on :80.
// Per-app documentation lives on the docs site, one page per app.
// Derived from the manifest's docs entry so there is no second place to update.
const docsUrlFor = (app) => {
  const docs = (MANIFEST.apps || []).find((a) => a.name === "docs");
  if (!docs || !docs.port) return null;
  const scheme = MANIFEST.scheme || "https";
  return `${scheme}://${MANIFEST.project}-${docs.port}.${MANIFEST.domain}/${app.name}.html`;
};

const urlFor = (app) => {
  const scheme = MANIFEST.scheme || "https";
  const port = app.port ?? 80;
  return `${scheme}://${MANIFEST.project}-${port}.${MANIFEST.domain}`;
};

// --- boot -------------------------------------------------------------------

async function boot() {
  try {
    const res = await fetch("manifest.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`manifest.json returned ${res.status}`);
    MANIFEST = await res.json();
  } catch (err) {
    document.getElementById("grid").innerHTML =
      `<p class="error">Could not load <code>manifest.json</code>: ${err.message}</p>`;
    return;
  }

  renderFilters();
  renderGrid();
  renderCounts();
  probeDns(); // async; updates the banner when it settles
}

// --- DNS probe --------------------------------------------------------------
// A no-cors fetch resolves (opaquely) if the host is reachable and rejects on a
// DNS/network failure. We can't read the response — we don't need to. We only
// want to know whether the browser can resolve the name at all.

async function probeDns() {
  const banner = document.getElementById("dns-banner");
  const live = MANIFEST.apps.filter((a) => a.status === "live");

  if (live.length === 0) {
    banner.className = "banner banner--warn";
    banner.innerHTML = "<strong>No apps deployed yet.</strong>";
    return;
  }

  const target = urlFor(live[0]);

  try {
    await fetch(target, { mode: "no-cors", cache: "no-store" });
    DNS_OK = true;
    banner.className = "banner banner--ok";
    banner.innerHTML =
      `<strong>Subdomain routing is working.</strong> Previews will load normally.`;
  } catch {
    DNS_OK = false;
    banner.className = "banner banner--warn";
    banner.innerHTML = `
      <strong>Previews aren't loading.</strong>
      <span>
        Routing is by PORT, so the usual cause is an app bound to
        <code>127.0.0.1</code> instead of <code>0.0.0.0</code> — the platform
        reaches <code>container:{port}</code> directly, and a loopback-only
        listener refuses the connection (that's a 502). Check over SSH:
      </span>
      <code class="cmd">ss -tlnp "sport = :${live[0].port ?? 80}"   # must show 0.0.0.0, not 127.0.0.1</code>
      <span>
        If it shows <code>0.0.0.0</code> and previews still fail, it's a DNS gap
        for <code>*.${MANIFEST.domain}</code> from this browser — the tiles and
        links still work.
      </span>`;
  }

  // Re-render so tiles can reflect what we learned.
  renderGrid();
}

// --- filters ----------------------------------------------------------------

function renderFilters() {
  const cats = [...new Set(MANIFEST.apps.map((a) => a.category))].sort(
    (a, b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b)
  );

  const el = document.getElementById("filters");
  el.innerHTML = "";

  const mk = (value, label) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.className = "chip" + (activeFilter === value ? " chip--on" : "");
    b.addEventListener("click", () => {
      activeFilter = value;
      renderFilters();
      renderGrid();
    });
    el.appendChild(b);
  };

  mk("all", "all");
  mk("live", "live only");
  cats.forEach((c) => mk(c, c));
}

function renderCounts() {
  const by = (s) => MANIFEST.apps.filter((a) => a.status === s).length;
  document.getElementById("counts").innerHTML = `
    <span class="dot dot--live"></span>${by("live")} live
    <span class="dot dot--todo"></span>${by("todo")} todo
    <span class="dot dot--blocked"></span>${
      by("blocked") + by("needs-scoping")
    } blocked`;
}

// --- grid -------------------------------------------------------------------

function visibleApps() {
  if (activeFilter === "all") return MANIFEST.apps;
  if (activeFilter === "live")
    return MANIFEST.apps.filter((a) => a.status === "live");
  return MANIFEST.apps.filter((a) => a.category === activeFilter);
}

function renderGrid() {
  const grid = document.getElementById("grid");
  const apps = [...visibleApps()].sort((a, b) => {
    const s = STATUS_ORDER[a.status] - STATUS_ORDER[b.status];
    if (s !== 0) return s;
    const c =
      CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category);
    if (c !== 0) return c;
    return a.label.localeCompare(b.label);
  });

  if (apps.length === 0) {
    grid.innerHTML = `<p class="loading">Nothing matches that filter.</p>`;
    return;
  }

  grid.innerHTML = "";
  apps.forEach((app) => grid.appendChild(tile(app)));
}

function tile(app) {
  const el = document.createElement("article");
  el.className = `tile tile--${app.status}`;

  const url = urlFor(app);
  const isLive = app.status === "live";

  const meta = [app.category, app.language, app.port ? `:${app.port}` : null]
    .filter(Boolean)
    .join(" · ");

  el.innerHTML = `
    <header class="tile__head">
      <h3>${app.label}</h3>
      <span class="status status--${app.status}">${app.status}</span>
    </header>
    <p class="tile__meta">${meta}</p>
    <p class="tile__desc">${app.description || ""}</p>
    ${
      app.blocker
        ? `<p class="tile__blocker"><strong>Blocked:</strong> ${app.blocker}</p>`
        : ""
    }
    <div class="tile__preview" data-preview></div>
    <footer class="tile__foot">
      ${
        isLive
          ? `<button type="button" class="btn" data-load>load preview</button>
             <a class="link" href="${url}" target="_blank" rel="noopener">open ↗</a>` +
             (docsUrlFor(app) && app.status === "live"
               ? ` <a class="link" href="${docsUrlFor(app)}" target="_blank" rel="noopener">instructions ↗</a>`
               : "")
          : `<span class="muted">not deployed</span>`
      }
    </footer>`;

  if (isLive) {
    el.querySelector("[data-load]").addEventListener("click", (e) => {
      loadPreview(el, app, e.currentTarget);
    });
  }

  return el;
}

// Insert the iframe only when asked. If DNS is known-bad, say so up front
// rather than rendering a browser error page inside the tile.
function loadPreview(el, app, btn) {
  const slot = el.querySelector("[data-preview]");
  btn.disabled = true;
  btn.textContent = "loading…";

  if (!DNS_OK) {
    slot.innerHTML = `
      <div class="preview-fail">
        <strong>Preview unavailable</strong>
        <span>
          <code>${MANIFEST.project}-${app.port ?? 80}.${MANIFEST.domain}</code>
          isn't reachable from this browser. Most often the app is bound to
          127.0.0.1 instead of 0.0.0.0; otherwise it's a DNS gap.
        </span>
      </div>`;
    btn.textContent = "preview unavailable";
    return;
  }

  const frame = document.createElement("iframe");
  frame.src = urlFor(app);
  frame.title = `${app.label} preview`;
  frame.loading = "lazy";
  slot.innerHTML = "";
  slot.appendChild(frame);
  btn.textContent = "preview loaded";
}

boot();
