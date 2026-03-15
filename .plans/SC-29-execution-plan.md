# SC-29 Execution Plan: Production Build

## FastAPI Static Serving + SPA Fallback

Add to `backend/src/szimplacoffee/main.py`:
```python
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = Path(__file__).parents[4] / "frontend" / "dist"

# After all API routes are mounted...

# Mount static assets (CSS, JS, images)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

# SPA catch-all: all non-API routes return index.html for React Router
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Don't intercept API routes
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"error": "Frontend not built. Run scripts/build.sh"}
```

## `scripts/build.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🏗️  Building SzimplaCoffee..."

# 1. Build frontend
echo "📦 Building React frontend..."
cd "$REPO_ROOT/frontend"
npm ci
npm run build
echo "✓ Frontend built: frontend/dist/"

# 2. Start backend (serves built frontend)
echo "🚀 Starting production server..."
cd "$REPO_ROOT/backend"
pip install -e . --quiet
uvicorn szimplacoffee.main:app --host 0.0.0.0 --port 8000

echo "✓ Server running at http://localhost:8000"
```

## `scripts/dev.sh` (updated)
```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-dev}"

if [ "$MODE" = "prod" ]; then
  exec "$REPO_ROOT/scripts/build.sh"
fi

echo "🔧 Starting SzimplaCoffee in DEV mode..."

# Start backend (hot-reload)
cd "$REPO_ROOT/backend"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✓ Backend started (PID $BACKEND_PID) → http://localhost:8000"

# Wait for backend to be ready
sleep 1

# Generate TypeScript client from OpenAPI
if [ -d "$REPO_ROOT/frontend" ] && [ -f "$REPO_ROOT/frontend/package.json" ]; then
  cd "$REPO_ROOT/frontend"
  npm run gen:api 2>/dev/null && echo "✓ TypeScript client generated" || echo "⚠ gen:api skipped"
  
  # Start frontend dev server
  npm run dev &
  FRONTEND_PID=$!
  echo "✓ Frontend started (PID $FRONTEND_PID) → http://localhost:5173"
fi

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID ${FRONTEND_PID:-} 2>/dev/null; exit" INT TERM
wait
```

## Update pyproject.toml
Add back aiofiles for async FileResponse:
```toml
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
    "httpx>=0.27",
    "aiofiles>=24.0",  # For async static file serving
]
```

## Verify Production Build
```bash
# Build and start
bash scripts/build.sh &
sleep 5

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/dashboard | python3 -m json.tool

# Test SPA
curl -s http://localhost:8000/ | grep '<div id="root">'
curl -s http://localhost:8000/merchants | grep '<div id="root">'  # SPA fallback

# Test that API routes don't trigger SPA
curl http://localhost:8000/api/v1/merchants | python3 -m json.tool
```
