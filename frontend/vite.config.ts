import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api/* to the FastAPI backend.
// Inside docker compose this is `http://api:8000` (compose service hostname).
// On host (`npm run dev` directly) it's `http://localhost:8000`.
const API_PROXY_TARGET = process.env.VITE_API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // Vite binds 127.0.0.1 by default; in container we override via CLI
    // (--host 0.0.0.0 in CMD), but document the intent here too.
    host: true,
    proxy: {
      "/api": API_PROXY_TARGET,
    },
  },
});
