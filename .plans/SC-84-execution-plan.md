# SC-84 Execution Plan

## Goal
Preserve recommendation context through purchase success and revisit flows so users can recognize and reopen the originating recommendation after saving a purchase.

## Context
SC-81 added recommendation-to-purchase handoff and SC-80 surfaces saved purchase linkage. This ticket follows by tightening the recommendation-aware revisit experience without expanding backend scope.

## Files / Areas Expected to Change
- `frontend/src/routes/purchases.lazy.tsx` — route search/state handling for recommendation-aware entry
- `frontend/src/components/purchases/PurchaseDetailDrawer.tsx` — contextual copy/navigation for linked recommendations
- `frontend/src/components/purchases/PurchaseHistoryList.tsx` — read-only reference for row-level linkage treatment
- `frontend/src/routes/recommendations.lazy.tsx` — read-only reference for existing handoff source behavior
- `frontend/src/api/schema.d.ts` — read-only contract reference

## Implementation Steps
1. Inspect the existing recommendation-to-purchase handoff and purchase save/revisit behavior.
2. Identify the smallest UI surface for recommendation-aware success or context copy.
3. Add or preserve navigation back to the linked recommendation when `recommendation_run_id` exists.
4. Confirm non-recommendation purchase flows remain unchanged.
5. Run `cd frontend && npm run build`.

## Risks / Notes
- Sequence after SC-80 to avoid overlapping linkage-surface changes.
- Avoid broad purchase-form redesign or speculative persistence work.
- Reuse existing route search/state patterns instead of introducing a new flow model.

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend/API changes
- Funnel analytics
- Long-term attribution persistence beyond existing fields
