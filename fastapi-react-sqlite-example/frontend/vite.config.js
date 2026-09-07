import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PRODUCTION (what deploys): `npm run build` emits dist/, served by the FastAPI
// backend on one port. DEV: `npm run dev` runs Vite on 5179 and proxies /api/*
// to the backend on 8003 (backend must be running). See §8 for host/allowedHosts.
export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    port: 5179,
    strictPort: true,
    host: true, // bind 0.0.0.0 — required if the dev server is exposed (§8)
    allowedHosts: [".example.com"], // (§8)
    proxy: {
      "/api": "http://127.0.0.1:8003",
    },
  },
});
