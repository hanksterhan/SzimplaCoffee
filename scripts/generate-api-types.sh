#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Generating OpenAPI spec from FastAPI..."
cd "$REPO_ROOT/backend"
# Use uv run to ensure deps from uv.lock are available; falls back to python3
if command -v uv &>/dev/null; then
  PYTHON="uv run python3"
else
  PYTHON="python3"
fi
$PYTHON -c "
import json, sys
sys.path.insert(0, 'src')
from szimplacoffee.main import app
spec = app.openapi()
with open('$REPO_ROOT/frontend/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2, default=str)
print(f'Written to frontend/openapi.json ({len(json.dumps(spec))} bytes)')
"

echo "Generating TypeScript types..."
cd "$REPO_ROOT/frontend"
npx openapi-typescript openapi.json -o src/api/schema.d.ts

echo "Done! TypeScript types at frontend/src/api/schema.d.ts"
