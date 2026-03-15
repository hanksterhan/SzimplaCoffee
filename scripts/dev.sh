#!/usr/bin/env bash
set -euo pipefail

# Start backend
cd "$(dirname "$0")/../backend"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend will be added in SC-18
echo "Backend running on http://localhost:8000 (PID $BACKEND_PID)"
wait
