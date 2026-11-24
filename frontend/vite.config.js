import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server only (npm run dev): proxies API and WebSocket to a locally running backend.
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            "/api": "http://localhost:8000",
            "/health": "http://localhost:8000",
            "/ws": { target: "ws://localhost:8000", ws: true },
        },
    },
});
