# SC-42 Execution Plan: Code Splitting

## Execution
1. Convert route files to use TanStack Router `.lazy.tsx` convention for automatic code splitting
2. Move heavy imports (Recharts) to only the routes that use them
3. Add manual chunks in vite.config.ts: vendor chunk for react/tanstack, ui chunk for shadcn
4. Add rollup-plugin-visualizer for dev-time bundle analysis
5. Verify: `npm run build` → check dist/assets/ → initial chunk <300KB gzipped
