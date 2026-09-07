import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The port is set here as well as in package.json so that `vite` picks up 5174
// no matter how it's launched. strictPort makes Vite fail loudly if 5174 is
// taken, instead of silently sliding to the next free port — important when a
// reverse proxy is pointed at a fixed port.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    host: "127.0.0.1",
  },
  preview: {
    port: 5174,
    strictPort: true,
  },
});
