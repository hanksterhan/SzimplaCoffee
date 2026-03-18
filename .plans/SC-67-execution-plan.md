# SC-67 Execution Plan

## Goal
Add explain_scores flag to the recommendation API — backend only.

## Context
Frontend explain toggle is SC-77. Split to keep each cycle focused.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/recommendations.py`
- `backend/src/szimplacoffee/api/recommendations.py`
- `backend/src/szimplacoffee/schemas/recommendations.py`

## Implementation Steps
1. Add `explain_scores: bool = False` to RecommendationRequest
2. When explain_scores=True, populate `score_breakdown` dict per candidate
3. Add `filtered_candidates` list with `filter_reason` per excluded candidate
4. Update Pydantic response schemas
5. Add pytest tests for explain mode output

## Verification
- `cd backend && .venv/bin/pytest tests/ -q`
- `cd backend && .venv/bin/ruff check src/ tests/`

## Out of Scope
- Frontend toggle (SC-77)
