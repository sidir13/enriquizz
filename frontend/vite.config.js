import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ──────────────────────────────────────────────────────────────────────────────
// En développement local, le proxy redirige /api → backend FastAPI (port 8000)
// ce qui évite les problèmes CORS en local et évite de coder l'URL en dur.
// En production sur Render, la variable d'env VITE_API_URL est utilisée (App.jsx)
// ──────────────────────────────────────────────────────────────────────────────
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
