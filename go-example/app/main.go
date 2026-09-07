// go environment example — bare Go, standard library only.
//
// The Go counterpart to the `nodejs`, `python` and `c_cpp` rows: no framework,
// no dependencies, nothing to fetch. Just net/http from the standard library,
// compiled to a single static binary.
//
// Binds TCP 3009 on 0.0.0.0 (CLAUDE.md §8). The platform routes
// my-container-3009.example.com straight to container:3009, so a
// 127.0.0.1-only listener would return 502 at the edge.
// NOTE: :3009 is a PROPOSED port (continues the 300x environments block after
// c_cpp 3007 and python 3008) — confirm with Anthony.
//
// Build & run:
//
//	go build -o server main.go && ./server
//
// The binary must be COMPILED ON THE CONTAINER — a macOS build will not run on
// Linux. deploy-all.sh does this automatically via the `gobuild` prep step.
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
)

const appName = "go"

// env returns the environment variable k, or def when it is unset or empty.
// deploy.sh sets PORT and HOST on the systemd unit; the defaults here mean the
// app is still correct when run by hand.
func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func page(host, port string) string {
	hostname, err := os.Hostname()
	if err != nil {
		hostname = "unknown"
	}
	return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>` + appName + ` &mdash; hello world</title>
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
    <h1>&#128075; hello from <code>` + appName + `</code></h1>
    <div>bare Go &middot; stdlib net/http &middot; no framework, no dependencies</div>
    <div class="meta">
      served by ` + hostname + ` &middot; ` + runtime.Version() + `<br>
      compiled binary listening on ` + host + `:` + port + ` &middot;
      <a href="/health" style="color:#7dd3fc">/health</a>
    </div>
  </div>
</body>
</html>`
}

func main() {
	port := env("PORT", "3009")
	host := env("HOST", "0.0.0.0") // bind all interfaces — required (§8)
	addr := host + ":" + port

	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(map[string]string{
			"app":    appName,
			"status": "ok",
			"go":     runtime.Version(),
		}); err != nil {
			log.Printf("health encode failed: %v", err)
		}
	})

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		fmt.Fprint(w, page(host, port))
	})

	log.Printf("[%s] listening on http://%s", appName, addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}
