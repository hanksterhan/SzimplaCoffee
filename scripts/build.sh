#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🏗️  Building SzimplaCoffee for production..."

# 1. Build the React frontend
echo ""
echo "📦 Building React frontend..."
cd "$REPO_ROOT/frontend"
npm ci --silent
npm run build
echo "✓ Frontend built → frontend/dist/"

# 2. Summary
echo ""
echo "✅ Build complete!"
echo ""
echo "To start the production server:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  cd $REPO_ROOT/backend"
echo "  uvicorn szimplacoffee.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  App will be available at http://localhost:8000"
echo "  API docs at http://localhost:8000/docs"
