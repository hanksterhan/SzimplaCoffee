#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO_ROOT/.venv"

# Ensure venv exists
if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV"
  source "$VENV/bin/activate"
  echo "Installing backend dependencies..."
  cd "$REPO_ROOT/backend" && pip install -e . && cd "$REPO_ROOT"
else
  source "$VENV/bin/activate"
fi

# Build frontend
echo "Building frontend..."
cd "$REPO_ROOT/frontend"
npm ci
npm run build

echo ""
echo "☕ Build complete!"
echo "   Frontend: $REPO_ROOT/frontend/dist/"
echo ""
echo "Start with:"
echo "   source .venv/bin/activate"
echo "   cd backend && uvicorn szimplacoffee.main:app --port 8000"
