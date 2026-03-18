# SC-84 — Recommendation Context Preservation in Purchase Revisit Flow

**Delivered:** 2026-03-18T19:25:00Z

## What Changed

### New file: `frontend/src/components/purchases/PurchaseDetailDrawer.tsx`
A click-to-open detail dialog for any purchase row. Shows:
- Full purchase facts (date, merchant, price, weight, $/lb, origin/process)
- Recommendation linkage context block (emerald-styled) with "Open recommendation run →" button
- Manual-log indicator when no run is linked
- Brew session count
- Edit/Delete action buttons

### Modified: `frontend/src/components/purchases/PurchaseForm.tsx`
- After a successful `addPurchase` with a `recommendationRunId`, instead of closing immediately, shows a **success state** dialog: "Purchase Saved ✓" with the run link and a "View recommendation →" button.
- Adds `useNavigate` to navigate directly to `/recommend?selectedRunId=N` from the success state.
- Cancellation and edit flows unchanged.

### Modified: `frontend/src/routes/purchases.lazy.tsx`
- Added `detailPurchase` state; table rows are now clickable (cursor-pointer) to open the drawer.
- Recommendation badge in the product column simplified to a compact emerald badge (🎯 run #N).
- Actions column uses `e.stopPropagation()` so edit/delete still work inline without opening drawer.
- `PurchaseDetailDrawer` wired into the dialogs section with onEdit/onDelete handlers.

## Why It Changed
SC-80 made recommendation linkage visible. SC-83 added a rec-linked filter toggle. SC-84 closes the loop: after saving from a recommendation, or when revisiting a linked purchase, users can now recognize and navigate back to the originating run without hunting through history.

## Verification
- `cd frontend && npm run build` — passed cleanly (4.42s, no errors, no TS errors)

## Surprises
- `PurchaseDetailDrawer.tsx` was referenced in the execution plan but the file didn't exist — created from scratch.
- The recommendation badge in the table was cleaned up (removed the inline "Open recommendation" text link; the drawer now owns that navigation).

## Follow-ups / Sharp Edges
- The success state in PurchaseForm currently requires manual dismiss ("Done" or "View recommendation →"). Could auto-dismiss after N seconds if desired.
- `PurchaseDetailDrawer` does not load fresh feedback detail inline — just shows count. A future ticket could expand feedback rows there too.
