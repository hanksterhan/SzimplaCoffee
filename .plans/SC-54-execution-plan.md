# SC-54 Execution Plan

## Goal

Add a richer "wait" recommendation that triggers when current options are below a quality threshold, with a plain-English rationale explaining why to wait.

## Context

North-star says: "The product must be allowed to say wait. If current options are below the quality bar or if the best-value roasters are likely to run a known sale soon, the product should recommend waiting."

Currently `wait_recommendation=not bool(candidates)` — too simplistic.

## Files Expected to Change

- `backend/src/szimplacoffee/services/recommendations.py` — add wait threshold logic
- `backend/src/szimplacoffee/api/recommendations.py` — expose `wait_rationale` in response
- `frontend/src/routes/today.lazy.tsx` — display wait rationale
- `frontend/src/hooks/use-today.ts` — add `wait_rationale` to type

## Implementation Steps

1. Add `WAIT_SCORE_THRESHOLD = 0.35` constant in `recommendations.py`
2. In `build_recommendations()`: if best candidate score < threshold, add `wait_reason` to return
3. Add `wait_rationale: str | None` to `RecommendationResultResponse` schema
4. Update `create_recommendation` and `today_buying_brief` to populate `wait_rationale`
5. Update `today.lazy.tsx` to show rationale when `wait_recommendation=true`

## Risks / Notes

- Do not change the `wait_recommendation=not bool(candidates)` fallback — keep it as a secondary trigger
- The threshold value (0.35) is a first guess; can be adjusted based on experience

## Verification

- `pytest -q` — tests should include a test for threshold-based wait trigger
- `npm run build` — today page shows rationale

## Out of Scope

- Predictive sale forecasting
- Alert/notification system
