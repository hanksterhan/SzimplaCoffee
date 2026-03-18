# SC-78 — PurchaseForm recommendation linkage

## What changed
- Added an optional `recommendationRunId` prop to `PurchaseForm` and included it in the create/update payload when present.
- Extended the frontend purchase mutation types to allow `recommendation_run_id` before the generated OpenAPI types are refreshed.
- Added `/purchases` search validation so `/purchases?recommendationRunId=<id>` can open the form with hidden recommendation context.

## Why it changed
SC-70 added backend support for linking purchases to recommendation runs, but the purchases UI still could not submit that field. This closed the frontend half of that workflow without exposing a new manual entry field.

## Verification
- `cd frontend && npm run build`

## Notes / sharp edges
- `frontend/src/api/schema.d.ts` still lacks `recommendation_run_id`; the hook now uses a local type extension so the UI can ship before the next API type regeneration.
- No recommendation-page deep link was added in this ticket; the purchase route now accepts the context once another surface navigates with `recommendationRunId`.
