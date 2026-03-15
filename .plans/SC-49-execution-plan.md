# SC-49 Execution Plan

## Scope

Build historical deal facts and a biggest-sales endpoint that use actual price baselines rather than only latest compare-at hints.

## Out of Scope

- Today dashboard UI
- 500-merchant rollout
- Agentic extraction review workflows

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q`
- AC-2 → `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q`
- AC-3 → `cd backend && . .venv/bin/activate && pytest -q`

## Slice Boundaries

### S1 Materialize historical price facts
- Files modify: `backend/src/szimplacoffee/services/recommendations.py`, `backend/src/szimplacoffee/models.py`, `backend/tests/test_recommendations.py`
- Files read only: `backend/src/szimplacoffee/api/products.py`
- Prohibited changes: do not rely only on current compare-at fields

### S2 Expose biggest-sales API with reasons
- Files modify: `backend/src/szimplacoffee/api/recommendations.py`, `backend/tests/test_recommendations.py`
- Files read only: `backend/src/szimplacoffee/services/recommendations.py`
- Prohibited changes: do not return opaque scores without reason strings

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q`
- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
