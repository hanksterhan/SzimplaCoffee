# SC-81 — Recommendation-to-purchase handoff

## What changed
- Added a recommendation-page CTA that appears only when the active result has a `run_id`.
- Wired the CTA to navigate to `/purchases` with `recommendationRunId` in route search.
- Kept the handoff compatible with both freshly generated recommendation results and history-selected runs because both flows set `activeResult.run_id`.

## Why it changed
SC-78 taught the purchases flow to accept recommendation context, but the recommendations page still made users manually navigate away and risk losing attribution context. This closes the UX handoff gap with a single focused route transition.

## Verification
- `cd frontend && npm run build`

## Notes / sharp edges
- The CTA is intentionally scoped to run-level context only; it does not prefill product, price, or merchant details.
- Wait states and empty states remain unchanged because the CTA only renders when an active run id exists.
