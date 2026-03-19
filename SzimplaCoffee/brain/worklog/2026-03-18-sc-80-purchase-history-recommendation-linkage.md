# 2026-03-18 - SC-80 purchase history recommendation linkage

Completed SC-80 closeout work:

- surfaced recommendation linkage badges directly in purchase rows
- added a recommendation-aware banner when `/purchases` is opened from a recommendation handoff
- added a direct path back to the originating recommendation run
- taught `/recommend` to reopen a historical run from route search (`selectedRunId`)

Verification completed:

- `cd frontend && npm run build`
