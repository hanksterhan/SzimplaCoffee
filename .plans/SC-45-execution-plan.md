# SC-45 Execution Plan

## Scope

Make catalog stock/search behavior truthful by aligning UI claims and stock labels with actual backend data semantics.

## Out of Scope

- Normalized metadata faceting
- Historical deal intelligence
- Full server-side sorting redesign

## AC to Verification Mapping

- AC-1 → `cd frontend && npm run build`
- AC-2 → `cd backend && . .venv/bin/activate && pytest tests/test_api_products.py -q`
- AC-3 → `cd frontend && npm run build`

## Slice Boundaries

### S1 Make stock semantics truthful in product summaries
- Files modify: `backend/src/szimplacoffee/api/products.py`, `backend/src/szimplacoffee/schemas/products.py`, `backend/tests/test_api_products.py`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not conflate product presence with live inventory status

### S2 Align catalog UI messaging with backend truth
- Files modify: `frontend/src/routes/products.lazy.tsx`, `frontend/src/hooks/use-products.ts`
- Files read only: `frontend/src/routes/products.$productId.lazy.tsx`
- Prohibited changes: do not advertise unsupported search fields

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest tests/test_api_products.py -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
- `cd frontend && npm run build`
