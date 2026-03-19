# SC-81 Execution Plan

## Goal
Add a narrow recommendations-to-purchases handoff so a user can log a purchase directly from a recommendation run without losing `recommendationRunId` context.

## Context
SC-70 added backend purchase-to-recommendation persistence, and SC-78 taught `PurchaseForm` / the purchases route to accept `recommendationRunId`. The remaining gap is on the recommendations page: there is still no direct CTA that sends the user into the purchase flow with the run context attached.

## Files / Areas Expected to Change
- `frontend/src/routes/recommend.lazy.tsx` — render the CTA near active recommendation results and navigate with route search
- `frontend/src/routes/purchases.tsx` — read-only reference for route search parsing
- `frontend/src/routes/purchases.lazy.tsx` — read-only reference for form modal auto-open behavior

## Implementation Steps
1. Inspect the active result rendering path in `recommend.lazy.tsx`.
2. Add a purchase CTA only when `activeResult.run_id` is available.
3. Route to `/purchases` with `recommendationRunId` in search params.
4. Confirm the CTA works for both freshly requested and history-selected runs.
5. Run `cd frontend && npm run build`.

## Risks / Notes
- Keep scope limited to navigation handoff; do not prefill additional purchase fields.
- Avoid introducing a new route or modal flow.
- Preserve the empty-state and wait-state behavior.

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend/API changes
- Purchase conversion analytics
- Product-level purchase-form prefills
