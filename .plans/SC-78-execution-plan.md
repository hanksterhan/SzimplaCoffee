# SC-78 Execution Plan

## Goal
Update PurchaseForm to accept and submit an optional recommendationRunId.

## Context
Backend model and API updated in SC-70. This ticket is frontend-only.

## Files / Areas Expected to Change
- `frontend/src/components/purchases/PurchaseForm.tsx` — add optional prop
- `frontend/src/routes/purchases.lazy.tsx` — pass prop when opening from recommendation context

## Implementation Steps
1. Add `recommendationRunId?: number` to PurchaseFormProps
2. Include it in the form state and POST body
3. In purchases.lazy.tsx, if a recommendation run was active, pass its ID when opening the form
4. Run `npm run build` — verify clean

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend (SC-70)
- Showing recommendation linkage in the purchase history list
