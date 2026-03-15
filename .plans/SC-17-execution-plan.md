# SC-17 Execution Plan: OpenAPI Spec + TypeScript Client Generation

## Install Dependencies (frontend/package.json)
```json
{
  "devDependencies": {
    "openapi-typescript": "^7.0.0"
  },
  "dependencies": {
    "openapi-fetch": "^0.12.0"
  },
  "scripts": {
    "gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts"
  }
}
```

## `frontend/src/api/client.ts`
```typescript
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

// Typed convenience exports
export type ApiPaths = paths;
```

## `frontend/src/api/index.ts`
```typescript
export { api } from "./client";
export type {
  // Merchant types
  components,
  paths,
} from "./schema";

// Convenience type aliases from generated schema
export type MerchantSummary =
  components["schemas"]["MerchantSummary"];
export type MerchantDetail =
  components["schemas"]["MerchantDetail"];
export type ProductSummary =
  components["schemas"]["ProductSummary"];
export type ProductDetail =
  components["schemas"]["ProductDetail"];
export type DashboardStats =
  components["schemas"]["DashboardStats"];
export type CrawlRunSchema =
  components["schemas"]["CrawlRunSchema"];
export type RecommendationRunSchema =
  components["schemas"]["RecommendationRunSchema"];
export type MerchantCandidateSchema =
  components["schemas"]["MerchantCandidateSchema"];
```

## `frontend/src/env.d.ts`
```typescript
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}
```

## `frontend/.env.development`
```
VITE_API_BASE_URL=http://localhost:8000
```

## `frontend/.env.production`
```
VITE_API_BASE_URL=
```
(empty = same origin in production, FastAPI serves frontend)

## Generation Workflow
```bash
# Start backend
cd backend && uvicorn szimplacoffee.main:app --port 8000 &

# Generate types
cd frontend && npm run gen:api

# Verify
cd frontend && npx tsc --noEmit
```

## Update `scripts/dev.sh`
```bash
# After starting backend, auto-generate types
sleep 2  # wait for backend to start
cd frontend && npm run gen:api && echo "✓ TypeScript client generated"
```

## FastAPI OpenAPI Configuration in `main.py`
Ensure FastAPI has meaningful titles for generated types:
```python
app = FastAPI(
    title="SzimplaCoffee API",
    version="1.0.0",
    description="Coffee product aggregation and recommendation engine",
)
```
All Pydantic schemas need explicit `model_config = ConfigDict(...)` with no anonymous/auto names.
