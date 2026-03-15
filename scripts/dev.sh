#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔧 Starting SzimplaCoffee in DEV mode..."

# Start backend (hot-reload)
cd "$REPO_ROOT/backend"
export PATH="$HOME/.local/bin:$PATH"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✓ Backend started (PID $BACKEND_PID) → http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"

# Wait briefly for backend to initialize
sleep 1

# Regenerate TypeScript client from OpenAPI (best-effort)
if [ -d "$REPO_ROOT/frontend" ] && [ -f "$REPO_ROOT/frontend/package.json" ]; then
  cd "$REPO_ROOT/frontend"
  npm run gen:api 2>/dev/null && echo "✓ TypeScript client regenerated" || true

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

trap "kill $BACKEND_PID ${FRONTEND_PID:-} 2>/dev/null; exit 0" INT TERM
wait
