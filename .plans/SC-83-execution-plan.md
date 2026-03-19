# SC-83 Execution Plan

## Goal
Add a narrow recommendation-linked filter to the Purchases page so users can quickly review recommendation-driven buys after SC-80 surfaces the linkage in the UI.

## Context
SC-78 submits recommendation linkage, SC-80 surfaces it in purchase list/detail views, and this follow-on adds a lightweight auditing affordance without changing backend contracts.

## Files / Areas Expected to Change
- `frontend/src/routes/purchases.lazy.tsx` — determine where filter state should live
- `frontend/src/components/purchases/PurchaseHistoryList.tsx` — apply filtered rendering and filtered empty state
- `frontend/src/components/purchases/PurchaseDetailDrawer.tsx` — read-only reference for existing recommendation linkage presentation
- `frontend/src/hooks/use-purchases.ts` — read-only data source reference
- `frontend/src/api/schema.d.ts` — read-only contract reference

## Implementation Steps
1. Inspect existing Purchases page controls/state to find the narrowest place to add a recommendation-linked filter.
2. Add a lightweight filter control that defaults off.
3. Narrow visible purchases to rows with `recommendation_run_id` when the filter is enabled.
4. Add explicit empty-state copy for the filtered view.
5. Run `cd frontend && npm run build`.

## Risks / Notes
- Keep this sequenced after SC-80 so the filter builds on visible linkage rather than hidden data.
- Do not add backend filtering or analytics scope.
- Prefer client-side filtering unless the route already owns an appropriate search-state pattern.

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend/API filter changes
- Recommendation conversion dashboards
- Purchase editing or relinking
