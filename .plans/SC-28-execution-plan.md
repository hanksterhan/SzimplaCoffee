# SC-28 Execution Plan: Remove Jinja Templates and Old HTML Routes

## Step 1: Identify what to remove
```bash
# Find all Jinja2/template references
grep -rn "jinja\|Jinja\|templates\|StaticFiles\|HTMLResponse\|Jinja2Templates" backend/src/ --include="*.py"

# List template files
ls -la backend/src/szimplacoffee/templates/ 2>/dev/null || echo "already removed"
ls -la backend/src/szimplacoffee/static/ 2>/dev/null || echo "already removed"
```

## Step 2: Clean main.py
Remove these patterns from `backend/src/szimplacoffee/main.py`:
```python
# REMOVE these imports:
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# REMOVE template initialization:
templates = Jinja2Templates(directory="...")

# REMOVE static file mount:
app.mount("/static", StaticFiles(directory="..."), name="static")

# REMOVE all @app.get routes that return TemplateResponse or HTMLResponse
# Example to remove:
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {...})
```

## Step 3: Delete files
```bash
rm -rf backend/src/szimplacoffee/templates/
rm -rf backend/src/szimplacoffee/static/
```

## Step 4: Update pyproject.toml
```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
    "httpx>=0.27",
    # REMOVE: "jinja2>=3.1",
    # REMOVE: "aiofiles>=24.0",
]
```

## Step 5: Verify
```bash
cd backend
ruff check src/ tests/
pytest tests/ -v
python -c "from szimplacoffee.main import app; print('OK')"
```

## What to KEEP in main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.merchants import router as merchants_router
from .api.products import router as products_router
from .api.recommendations import router as recommendations_router
from .api.discovery import router as discovery_router
from .api.dashboard import router as dashboard_router

app = FastAPI(
    title="SzimplaCoffee API",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(merchants_router)
api_v1.include_router(products_router)
api_v1.include_router(recommendations_router)
api_v1.include_router(discovery_router)
api_v1.include_router(dashboard_router)
app.include_router(api_v1)

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Background crawl tasks are preserved (if any in main.py)
```
