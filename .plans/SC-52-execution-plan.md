# SC-52 Execution Plan

## Scope

Build the daily utility views that turn backend truth into a practical buying workflow.

## Out of Scope

- Full top-500 rollout
- Mobile-native UI
- Multi-user auth

## AC to Verification Mapping

- AC-1 → `cd frontend && npm run build`
- AC-2 → `cd frontend && npm run build`
- AC-3 → `cd backend && . .venv/bin/activate && pytest -q && cd ../frontend && npm run build`

## Slice Boundaries

### S1 Build Today dashboard and utility endpoints
- Files modify: `backend/src/szimplacoffee/api/recommendations.py`, `frontend/src/routes/`, `frontend/src/hooks/`
- Files read only: `backend/src/szimplacoffee/services/recommendations.py`
- Prohibited changes: do not optimize secondary views before the daily-buying workflow works

### S2 Add watch and review surfaces for crawl/metadata trust
- Files modify: `frontend/src/routes/`, `frontend/src/components/`, `backend/src/szimplacoffee/api/merchants.py`
- Files read only: `backend/src/szimplacoffee/services/crawlers.py`
- Prohibited changes: do not create a passive queue with no obvious actionability

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest -q`
- `cd frontend && npm run build`
