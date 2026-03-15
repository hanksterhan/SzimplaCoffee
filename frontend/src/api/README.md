# API Types

This directory contains auto-generated TypeScript types from the SzimplaCoffee FastAPI backend.

## `schema.d.ts`

This file is **generated** — do not edit it manually. It is created by running:

```bash
# From the repo root:
./scripts/generate-api-types.sh

# Or via npm script (from frontend/):
npm run generate-api-types
```

### Prerequisites

1. Python deps installed in the backend:
   ```bash
   cd backend && pip install -e ".[dev]"
   ```

2. Node deps installed in the frontend:
   ```bash
   cd frontend && npm install
   ```

### How it works

1. The script imports the FastAPI `app` from `szimplacoffee.main`
2. Calls `app.openapi()` to extract the OpenAPI 3.x JSON spec
3. Writes it to `frontend/openapi.json`
4. Runs `openapi-typescript` to convert the JSON spec into TypeScript type definitions at `frontend/src/api/schema.d.ts`

### Usage in components

```typescript
import type { paths, components } from './schema.d.ts';

// Example: type a MenuItem from the API
type MenuItem = components['schemas']['MenuItem'];

// Example: type a response from GET /menu
type MenuResponse = paths['/menu']['get']['responses']['200']['content']['application/json'];
```

> `openapi.json` and `schema.d.ts` are gitignored — regenerate them locally before developing.
