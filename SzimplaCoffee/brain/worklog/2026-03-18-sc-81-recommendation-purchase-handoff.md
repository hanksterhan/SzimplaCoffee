# 2026-03-18 - SC-81 recommendation-to-purchase handoff

Completed SC-81 closeout work:

- added a recommendations-page CTA that appears when the active result has a `run_id`
- routed that CTA to `/purchases?recommendationRunId=<id>` so purchase logging opens with recommendation context preserved
- kept the handoff working for both fresh recommendation results and history-selected runs because both populate `activeResult.run_id`
- preserved the existing empty and wait states by only rendering the CTA when recommendation context is available

Verification completed:

- `cd frontend && npm run build`
