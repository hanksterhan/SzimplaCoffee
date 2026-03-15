# SC-10 Execution Plan: Restructure repo into backend/frontend monorepo layout

## Goal
Move existing Python project into `backend/` subdirectory, create `frontend/` scaffold, and add a `scripts/dev.sh` for running both.

## Steps

### 1. Create directory structure
```bash
mkdir -p backend/src/szimplacoffee/services
mkdir -p backend/tests
mkdir -p frontend
mkdir -p scripts
```

### 2. Move Python source files
```bash
cp -r src/szimplacoffee/* backend/src/szimplacoffee/
cp -r tests/* backend/tests/
cp pyproject.toml backend/pyproject.toml
```

Update `backend/pyproject.toml`:
- Change `packages = [{include = "szimplacoffee", from = "src"}]`
- Update any path references

### 3. Update config.py DATABASE_URL
In `backend/src/szimplacoffee/config.py`, ensure DATABASE_URL resolves to the DB file:
```python
# Default: look for DB relative to backend/ or repo root
DATABASE_URL: str = f"sqlite:///{Path(__file__).parents[4] / 'szimplacoffee.db'}"
```

### 4. Create scripts/dev.sh
```bash
#!/usr/bin/env bash
set -e

# Start backend
cd "$(dirname "$0")/../backend"
uvicorn szimplacoffee.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend (once initialized)
if [ -f "../frontend/package.json" ]; then
  cd "../frontend"
  npm run dev &
  FRONTEND_PID=$!
fi

echo "Backend PID: $BACKEND_PID"
echo "Press Ctrl+C to stop all services"
trap "kill $BACKEND_PID ${FRONTEND_PID:-}; exit" INT TERM
wait
```

### 5. Create frontend scaffold
```bash
echo "# Frontend (React SPA — initialized in SC-18)" > frontend/README.md
touch frontend/.gitkeep
```

### 6. Update .gitignore
Add:
```
frontend/node_modules/
frontend/dist/
backend/__pycache__/
backend/.venv/
```

### 7. Verify
```bash
cd backend && pip install -e ".[dev]"
cd backend && pytest tests/ -v
cd backend && ruff check src/ tests/
```

## File Map (after move)
```
SzimplaCoffee/
├── backend/
│   ├── src/szimplacoffee/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── cli.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── bootstrap.py
│   │   └── services/
│   │       ├── crawlers.py
│   │       ├── discovery.py
│   │       ├── platforms.py
│   │       └── recommendations.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── README.md
├── scripts/
│   └── dev.sh
├── szimplacoffee.db
└── .gitignore
```
