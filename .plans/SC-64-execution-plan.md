# SC-64 Execution Plan

## Goal
Add metadata fill-rate counts (total_products, products_with_origin, products_with_process, products_with_roast_level) to the /api/v1/dashboard endpoint and render them in the Today view.

## Context
Without fill-rate visibility in the UI, it is impossible to monitor metadata pipeline progress or regression after parser improvements. This is a lightweight observability addition.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/api/dashboard.py`
- `frontend/src/routes/index.tsx`

## Implementation Steps
1. Inspect current dashboard.py — understand existing response structure and Pydantic schema
2. Add four count queries to the dashboard handler:
   ```python
   total_products = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
   with_origin = db.execute(text("SELECT COUNT(*) FROM products WHERE origin IS NOT NULL")).scalar()
   with_process = db.execute(text("SELECT COUNT(*) FROM products WHERE process IS NOT NULL")).scalar()
   with_roast = db.execute(text("SELECT COUNT(*) FROM products WHERE roast_level IS NOT NULL")).scalar()
   ```
3. Add fields to the Pydantic response schema (or DashboardResponse TypedDict)
4. Return computed values in the response
5. Run `npm run gen:api` if frontend uses generated schema types
6. Update `index.tsx` Today view to render fill rates:
   - "Origin: 47% | Process: 38% | Roast: 52%"
   - Use a simple grid or stat row
7. Run `npm run build` and verify no type errors

## Risks / Notes
- If dashboard response is untyped dict, skip schema update and add fields directly
- Frontend may need type update in schema.d.ts if using generated types
- Keep layout change minimal — add after existing stats, not a redesign

## Verification
```bash
curl -s http://localhost:8000/api/v1/dashboard | python -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('total_products'), d.get('products_with_origin'), d.get('products_with_process'), d.get('products_with_roast_level'))
"
cd frontend && npm run build 2>&1 | tail -5
```

## Out of Scope
- Historical fill rate trending
- Per-merchant metadata breakdown
- Alerts on fill rate regression
