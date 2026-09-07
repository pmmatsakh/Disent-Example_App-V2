// expressjs environment example — a minimal Express backend, no database.
// (Vanilla Node lives in the `nodejs` row; this one adds the Express framework.)
//
// Binds TCP 3006 on 0.0.0.0. The platform routes the public subdomain by PORT
// (my-container-3006.example.com -> container:3006), so the app MUST listen
// on 0.0.0.0, not 127.0.0.1 — otherwise the edge gets a 502. See CLAUDE.md §2/§8.
//
// NOTE: :3006 is a PROPOSED port (backend 8000s block) — confirm with Anthony.

import express from "express";
import os from "node:os";

const APP_NAME = "expressjs";
const PORT = process.env.PORT || 3006;
const HOST = process.env.HOST || "0.0.0.0"; // bind all interfaces — required (§8)

const app = express();

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
    <div>Node.js · Express · no database</div>
    <div class="meta">
      served by ${os.hostname()} · node ${process.version}<br>
      listening on ${HOST}:${PORT} · <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>`;

app.get("/health", (req, res) => {
  res.json({ app: APP_NAME, status: "ok", node: process.version });
});

app.get("/", (req, res) => {
  res.type("html").send(page());
});

app.listen(PORT, HOST, () => {
  console.log(`[${APP_NAME}] listening on http://${HOST}:${PORT}`);
});
