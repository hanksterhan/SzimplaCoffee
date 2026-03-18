# SC-77 Execution Plan

## Goal
Add an explain toggle to the Recommendations page that renders per-candidate score breakdowns.

## Context
Backend explain_scores support is added in SC-67. This ticket is frontend-only.

## Files / Areas Expected to Change
- `frontend/src/routes/recommend.lazy.tsx` — explain toggle + score breakdown render
- `frontend/src/hooks/use-recommendations.ts` — pass explain_scores in request

## Implementation Steps
1. Add `explainScores` boolean state to RecommendPage
2. Add checkbox "Explain scores" in the Configure section
3. Pass `explain_scores: explainScores` to `request.mutate()`
4. In the results card, if `score_breakdown` exists, render a collapsible `<details>` section
5. Run `npm run build` — verify clean

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend (SC-67)
- Persisting explain preference across sessions
