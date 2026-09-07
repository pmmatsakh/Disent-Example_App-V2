import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Two ways to run this frontend:
//
//  • PRODUCTION (what deploys): `npm run build` emits dist/, and the FastAPI
//    backend serves those files on its own port. One port, same origin, no CORS.
//
//  • DEV (optional, for hot reload): `npm run dev` runs the Vite dev server on
//    5177 and proxies /api/* to the backend on 8002 — so fetch("/api/hello")
//    still hits FastAPI while you edit with HMR. Requires the backend running.
export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    port: 5177,
    strictPort: true,
    host: true, // bind 0.0.0.0 — required if the dev server is exposed (§8)
    allowedHosts: [".example.com"], // (§8)
    proxy: {
      "/api": "http://127.0.0.1:8002",
    },
  },
});
