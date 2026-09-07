import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Tailwind v4 plugs straight into Vite (no separate PostCSS/tailwind.config
// needed) — the `tailwindcss()` plugin scans the classes used in your JSX.
//
// server.host + allowedHosts are REQUIRED for this to work through the platform
// edge (CLAUDE.md §8): bind all interfaces (host: true), and allow the
// .example.com host so Vite's dev server doesn't reject the proxied request.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3003,
    strictPort: true,
    host: true, // bind 0.0.0.0 — required (§8)
    allowedHosts: [".example.com"], // accept my-container-3003.example.com (§8)
  },
  preview: {
    port: 3003,
    strictPort: true,
  },
});
