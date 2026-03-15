#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Start backend
cd "$REPO_ROOT/backend"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo "Backend: http://localhost:8000 (PID $BACKEND_PID)"
echo "Frontend: http://localhost:5173 (PID $FRONTEND_PID)"
echo "Press Ctrl+C to stop both"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
