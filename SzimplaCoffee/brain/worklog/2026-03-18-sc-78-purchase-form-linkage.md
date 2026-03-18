# 2026-03-18 - SC-78 purchase form recommendation linkage

Completed SC-78 closeout work:

- added an optional `recommendationRunId` prop to `PurchaseForm`
- included `recommendation_run_id` in the purchase payload when recommendation context is present
- extended the frontend purchase mutation types locally so the UI can submit the new field before the next OpenAPI type regeneration
- added `/purchases` search validation so `/purchases?recommendationRunId=<id>` can auto-open the log-purchase dialog with hidden recommendation context
- created follow-on ticket SC-80 to surface recommendation linkage in the purchases UI after submission is live

Verification completed:

- `cd frontend && npm run build`
