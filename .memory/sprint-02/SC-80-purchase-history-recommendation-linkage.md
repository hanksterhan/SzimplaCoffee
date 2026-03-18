# SC-80 — Purchase history recommendation linkage

## What changed
- Extended the purchases UI to surface `recommendation_run_id` when a saved purchase is linked to a recommendation run.
- Added a recommendation-aware banner when the Purchases page is opened from the recommendation handoff flow.
- Added direct navigation from linked purchases back to `/recommend` and taught the recommendations route to reopen a selected historical run via `selectedRunId`.
- Tightened frontend purchase types so recommendation linkage is available to the purchases UI even before regenerated API types catch up.

## Why it changed
SC-78 and SC-81 created the hidden plumbing for recommendation-aware purchase logging, but users still could not audit which purchases came from which recommendation runs. This closes that visibility gap with a narrow frontend-only slice.

## Verification
- `cd frontend && npm run build`

## Notes / sharp edges
- The generated frontend API schema still lacks `recommendation_run_id` on `PurchaseSummary`/`PurchaseDetail`, so the hook types were locally augmented to keep the UI typed until the next API type regeneration.
- Reopening a linked recommendation depends on the run still appearing in recommendation history; if history pruning is added later, this flow will need a fallback.
