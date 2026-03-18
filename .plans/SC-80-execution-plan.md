# SC-80 Execution Plan

## Goal
Surface purchase-to-recommendation linkage in the purchases UI so recommendation-driven buys are auditable after SC-78 starts submitting `recommendation_run_id`.

## Context
SC-70 added backend persistence for purchase-to-recommendation linkage. SC-78 adds frontend form submission support. This follow-on ticket keeps scope tight: read existing purchase response data and render linkage where it already fits in the purchases UX.

## Files / Areas Expected to Change
- `frontend/src/routes/purchases.lazy.tsx` — confirm where purchase detail context and navigation live
- `frontend/src/components/purchases/PurchaseHistoryList.tsx` — render linked recommendation badge or affordance in list rows
- `frontend/src/components/purchases/PurchaseDetailDrawer.tsx` — show recommendation linkage detail/navigation when present
- `frontend/src/api/schema.d.ts` — read-only contract reference
- `frontend/src/hooks/use-purchases.ts` — read-only data-fetching reference

## Implementation Steps
1. Inspect the purchases list/detail components to find the narrowest place to surface recommendation linkage.
2. Add conditional rendering for purchases that include `recommendation_run_id`.
3. Add lightweight navigation or contextual text pointing to the linked recommendation run without introducing new routes.
4. Verify the UI still renders correctly when the field is null or absent.
5. Run `cd frontend && npm run build`.

## Risks / Notes
- Keep this blocked on SC-78 so the UI does not ship before the form can actually send linkage data.
- Avoid speculative backend changes or conversion analytics.
- Prefer minimal copy/badge affordances over a larger purchases UX redesign.

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend API/model changes
- Conversion analytics dashboards
- Editing recommendation linkage after purchase creation
