# SC-83 — Recommendation-Linked Purchase Filter

## What Changed
Added a `filterRecommendationLinked` boolean state to `purchases.lazy.tsx`. A "🎯 Rec-linked" toggle button in the filters bar client-side narrows the purchase list to rows where `recommendation_run_id != null`. The empty-state when filtered shows a recommendation-specific message with a "Show all purchases" escape hatch.

## Files Changed
- `frontend/src/routes/purchases.lazy.tsx` — added filter state, client-side filter, toggle button, empty-state copy

## Why
Follows SC-80 which first exposed `recommendation_run_id` in purchase rows. Once linkage is visible, users need a fast way to audit recommendation-driven purchases without scanning all history.

## Implementation Notes
- The filter is pure client-side; no backend API changes. `rawPurchases` holds the full API result; `purchases` (used for rendering) is the possibly-filtered view.
- The 🎯 button renders as `variant="default"` when active (solid) vs `"outline"` when off to make toggle state obvious.
- Reused the existing `recommendation_run_id` field already present on `PurchaseSummary` from the SC-80 hook changes.

## What Worked
Straight clean approach — build passed first try. The `PurchaseHistoryList.tsx` noted in the plan doesn't exist as a separate file (list is inline in the route); adapted accordingly.

## Follow-Up / Next
- SC-84: preserve recommendation context in purchase success/revisit flows — tightens up the return-to-recommendation flow.
