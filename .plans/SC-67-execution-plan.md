# SC-67 Execution Plan

## Goal
Add an optional explain_scores flag to the recommendation API. When true, return per-candidate score breakdown and filter elimination reasons.

## Context
Debugging recommendations is opaque without score visibility. Explain mode enables both developer debugging and user-facing transparency about why a coffee was or was not recommended.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/recommendations.py`
- `backend/src/szimplacoffee/api/recommendations.py`
- `frontend/src/routes/recommend.lazy.tsx`

## Implementation Steps
1. Add `explain_scores: bool = False` to recommendation request Pydantic schema
2. In recommendations.py, when explain_scores=True, collect per-candidate:
   ```python
   score_breakdown = {
       "quality_score": ...,
       "price_score": ...,
       "subscription_bonus": ...,
       "brew_penalty": ...,
       "inventory_adjustment": ...,
       "total": ...
   }
   ```
3. For filtered candidates, collect filter_reason:
   ```python
   filtered_candidates = [
       {"product_id": ..., "filter_reason": "trust_tier_below_threshold"},
       ...
   ]
   ```
4. Include both in response when explain_scores=True; exclude when False (no perf cost for normal requests)
5. Update API schema to reflect optional explain fields
6. Update recommend.lazy.tsx: add "Show Scores" toggle; when enabled, render collapsible score breakdown per card
7. npm run build to verify frontend

## Risks / Notes
- explain_scores=False must be the default — no breaking change to existing callers
- Keep score breakdown shallow (no nested objects per dimension) for readability
- Frontend: use a simple accordion or tooltip for breakdown; not a full redesign

## Verification
```bash
curl -s -X POST http://localhost:8000/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"current_inventory_grams": 0, "explain_scores": true}' \
  | python -c "import json,sys; d=json.load(sys.stdin); r=d.get('results',[]); print(r[0].get('score_breakdown') if r else 'no results')"
cd frontend && npm run build 2>&1 | tail -5
```

## Out of Scope
- Persisting explain data to DB
- Export or CSV of explain results
