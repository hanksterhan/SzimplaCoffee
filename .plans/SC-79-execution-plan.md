# SC-79 Execution Plan

## Goal
Render crawl health fields (last_crawl_at, product_count, metadata_pct) on Watch page merchant cards.

## Context
Backend API enriched in SC-74 and API types regenerated. This ticket is frontend-only.

## Files / Areas Expected to Change
- `frontend/src/routes/watch.lazy.tsx` — render new fields per card

## Implementation Steps
1. Confirm `schema.d.ts` has new fields (run `npm run gen:api` if not)
2. Add crawl health section to each merchant card:
   - Last crawled: relative time or "Never"
   - Products: count
   - Metadata: colored % badge
3. Run `npm run build` — verify clean

## Risks / Notes
- If API isn't running, gen:api will fail — use existing schema.d.ts and add types manually

## Verification
- `cd frontend && npm run build`

## Out of Scope
- Backend (SC-74)
- Crawl history drill-down
