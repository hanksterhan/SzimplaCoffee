import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-vite-plugin";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [
    react(),
    TanStackRouterVite(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Core React runtime
          "vendor-react": ["react", "react-dom"],
          // TanStack Router + Query
          "vendor-tanstack": [
            "@tanstack/react-router",
            "@tanstack/react-query",
          ],
          // Recharts (heavy, only used in charts)
          "vendor-recharts": ["recharts"],
          // UI components (radix + shadcn)
          "vendor-ui": [
            "@radix-ui/react-dialog",
            "@radix-ui/react-select",
            "@radix-ui/react-tabs",
            "@radix-ui/react-tooltip",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-separator",
          ],
          // Command palette (cmdk)
          "vendor-cmdk": ["cmdk"],
          // Toast
          "vendor-sonner": ["sonner"],
        },
      },
    },
  },
});
