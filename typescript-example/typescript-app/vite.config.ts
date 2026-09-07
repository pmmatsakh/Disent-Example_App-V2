import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// server.host + allowedHosts are REQUIRED to work through the platform edge
// (CLAUDE.md §8): bind all interfaces (host: true), and allow the .example.com
// host so Vite's dev server doesn't reject the proxied request.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3004,
    strictPort: true,
    host: true, // bind 0.0.0.0 — required (§8)
    allowedHosts: [".example.com"], // accept my-container-3004.example.com (§8)
  },
  preview: {
    port: 3004,
    strictPort: true,
  },
});
