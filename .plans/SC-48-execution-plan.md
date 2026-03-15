# SC-48 Execution Plan

## Scope

Move shopping-relevant catalog filtering and sorting into the backend so the full corpus can be queried truthfully.

## Out of Scope

- Historical deal scoring implementation
- Today dashboard UI
- Merchant discovery scale-out

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest tests/test_api_products.py -q`
- AC-2 → `cd backend && . .venv/bin/activate && pytest tests/test_api_products.py -q`
- AC-3 → `cd frontend && npm run build`

## Slice Boundaries

### S1 Expand products API query model
- Files modify: `backend/src/szimplacoffee/api/products.py`, `backend/src/szimplacoffee/schemas/products.py`, `backend/tests/test_api_products.py`, `frontend/src/api/schema.d.ts`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not preserve client-side corpus-truth sorting as the primary path

### S2 Rewire frontend catalog controls to backend query state
- Files modify: `frontend/src/hooks/use-products.ts`, `frontend/src/routes/products.lazy.tsx`
- Files read only: `frontend/src/components/ui/dropdown-menu.tsx`
- Prohibited changes: do not regress current dropdown UX unnecessarily

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest tests/test_api_products.py -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
- `cd frontend && npm run build`
