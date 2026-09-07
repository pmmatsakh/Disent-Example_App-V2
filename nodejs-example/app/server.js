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
