# SC-53 Execution Plan

## Scope

Build the explicit merchant registry and quality gates needed to scale deliberately toward top-500 coverage.

## Out of Scope

- Crawling all 500 merchants immediately
- Distributed infrastructure
- Marketing/public ranking features

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-2 → `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q`
- AC-3 → `rg -n 'watchlist|trusted|candidate|low-value|manual-only|Tier A|Tier B|Tier C|Tier D' README.md backend .plans SzimplaCoffee/brain -S`

## Slice Boundaries

### S1 Represent registry states and inclusion thresholds
- Files modify: `backend/src/szimplacoffee/models.py`, `backend/src/szimplacoffee/api/merchants.py`, `backend/src/szimplacoffee/services/discovery.py`
- Files read only: `backend/src/szimplacoffee/services/recommendations.py`
- Prohibited changes: do not let low-quality merchants influence flagship daily-buying views

### S2 Document top-500 rollout policy
- Files modify: `README.md`, `SzimplaCoffee/brain/backlog/now-next-later.md`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not frame discovery count as quality coverage

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q`
- `rg -n 'watchlist|trusted|candidate|low-value|manual-only|Tier A|Tier B|Tier C|Tier D' README.md backend .plans SzimplaCoffee/brain -S`
