import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Served by editor/serve.py at /flow/ in production, and by the Vite dev
// server (with an API proxy to the Python backend) during development.
export default defineConfig({
  base: "/flow/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8765",
      "/templates": "http://127.0.0.1:8765",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
