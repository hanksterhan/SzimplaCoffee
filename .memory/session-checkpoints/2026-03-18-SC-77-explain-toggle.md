# SC-77 Delivery Checkpoint — 2026-03-18

## Task
SC-77: Add explain toggle to Recommendations page UI

## What Changed
- `frontend/src/api/schema.d.ts`: Added `FilteredCandidateOut`, `ScoreBreakdown` types; added `explain_scores?: boolean` to `RecommendationRequestPayload`; added `score_breakdown?` to `RecommendationCandidateOut`; added `filtered_candidates?` to `RecommendationResultResponse`
- `frontend/src/hooks/use-recommendations.ts`: Exported `FilteredCandidateOut` and `ScoreBreakdown` types
- `frontend/src/routes/recommend.lazy.tsx`: 
  - Added `explainScores` state
  - Added "Explain scores" checkbox in Configure section
  - Added `ScoreBreakdownPanel` component (collapsible `<details>` with per-dimension bars + weights)
  - `ResultCard` now accepts `explainScores` prop and renders breakdown when available
  - Filtered candidates table shown below results when explain mode on and data present

## Verification
- `cd frontend && npm run build` → ✓ clean in 4.36s
- `cd backend && pytest tests/` → 132 passed

## Notes
- Schema types added manually (backend was running but schema gen not wired in CI); types accurately mirror backend Pydantic models from SC-67
- Breakdown uses `<details>/<summary>` for native collapsible — no extra deps
- `score_breakdown` is only populated server-side when `explain_scores=True`; missing from history replays (stored JSON strips it per SC-67 design)

## Commit
cf9b495 — pushed to main
