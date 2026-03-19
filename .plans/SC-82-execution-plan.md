# SC-82 Execution Plan

## Goal
Make the Watch page more operationally useful by surfacing stale and failed crawl status directly in merchant rows using already-available API fields.

## Context
SC-74 added crawl health fields to the merchant API, and the Watch page already renders some of them (`last_crawl_at`, `product_count`, `metadata_pct`). The remaining gap is interpretation: users still have to inspect timestamps and infer which merchants are stale or had a failed crawl.

## Files / Areas Expected to Change
- `frontend/src/routes/watch.lazy.tsx` — derive crawl-status states and render badges/copy
- `frontend/src/hooks/use-watchlist.ts` — read-only reference for fetched merchant shape
- `frontend/src/api/schema.d.ts` — read-only contract reference if field names need confirmation

## Implementation Steps
1. Inspect the existing merchant row rendering in `watch.lazy.tsx`.
2. Add a small helper that classifies merchants into at least: never crawled, failed last crawl, stale, healthy/neutral.
3. Render concise status badges in the existing merchant metadata row.
4. Ensure the new indicators do not interfere with trust controls or watchlist actions.
5. Run `cd frontend && npm run build`.

## Risks / Notes
- Keep thresholds simple and explicit in the route file; avoid premature abstraction.
- Do not add backend work or automatic recrawl actions in this ticket.
- Preserve the current compact row layout.

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend API/schema changes
- Crawl history drill-downs
- Watch page recrawl buttons
