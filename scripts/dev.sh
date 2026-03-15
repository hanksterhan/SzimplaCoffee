#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO_ROOT/.venv"

# Ensure venv exists
if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV"
  echo "Installing backend dependencies..."
  source "$VENV/bin/activate"
  cd "$REPO_ROOT/backend" && pip install -e . && cd "$REPO_ROOT"
else
  source "$VENV/bin/activate"
fi

# Generate API types if frontend exists
if [ -d "$REPO_ROOT/frontend/node_modules" ]; then
  echo "Regenerating API types..."
  bash "$REPO_ROOT/scripts/generate-api-types.sh" 2>/dev/null || true
fi

# Start backend
cd "$REPO_ROOT/backend"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "☕ SzimplaCoffee Dev Mode"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
