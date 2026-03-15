# SC-18 Execution Plan: Vite + React + TypeScript Scaffold

## `frontend/package.json`
```json
{
  "name": "szimplacoffee-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-router": "^1.0.0",
    "@tanstack/react-query": "^5.0.0",
    "openapi-fetch": "^0.12.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@tanstack/router-vite-plugin": "^1.0.0",
    "@tanstack/react-query-devtools": "^5.0.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "openapi-typescript": "^7.0.0"
  }
}
```

## `frontend/vite.config.ts`
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { TanStackRouterVite } from "@tanstack/router-vite-plugin";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    react(),
    TanStackRouterVite(),
    tailwindcss(),
  ],
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
```

## `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

## `frontend/src/main.tsx`
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { routeTree } from "./routeTree.gen";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

const router = createRouter({
  routeTree,
  context: { queryClient },
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>
);
```

## `frontend/src/routes/__root.tsx`
```tsx
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";

interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => <Outlet />,
});
```

## `frontend/src/routes/index.tsx`
```tsx
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: () => (
    <div className="p-8">
      <h1 className="text-3xl font-bold">☕ SzimplaCoffee</h1>
      <p className="text-muted-foreground mt-2">Coffee sourcing dashboard</p>
    </div>
  ),
});
```

## `frontend/src/index.css`
```css
@import "tailwindcss";

:root {
  font-family: system-ui, sans-serif;
}
```

## Route Files (placeholder)
Create placeholder files for: merchants, products, recommendations, discovery
Each exports `Route = createFileRoute("/path")({ component: () => <div>...</div> })`
