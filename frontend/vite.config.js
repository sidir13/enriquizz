import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En dev : Vite proxy /api et /ws vers FastAPI (port 8000).
// En prod : le build sort dans backend/static, servi par le même processus uvicorn.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
