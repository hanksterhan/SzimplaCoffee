# SC-113 — Purchase History Intelligence Panel

**Delivered:** 2026-03-20T15:10:00Z

## What Changed

- New endpoint `GET /api/v1/history/purchase-stats` (separate from existing `/purchases/stats`)
- New schemas: `BuyingPatternStats`, `TopRoaster`
- 4 new backend tests; total now 358 (all pass)
- `useBuyingPatterns()` hook in `use-purchases.ts`
- `PurchaseStatsCard` component at `frontend/src/components/PurchaseStatsCard.tsx`
- `PurchaseStatsCard` integrated into Purchases page

## Design Decisions

- Used a different route (`/history/purchase-stats`) from the existing `/purchases/stats`
  to avoid route conflicts (FastAPI path parameter collision with `/purchases/{id}`)
- `avg_grams_per_week` returns null if fewer than 2 purchase rows exist
- top_roasters capped at 3

## What Future Agents Should Know

- If adding more stats to BuyingPatternStats, extend the schema and rerun `npm run gen:api`
- The existing `/purchases/stats` endpoint has separate fields (total_purchases, total_spent_cents,
  avg_price_per_lb_cents, favorite_merchant_id) — keep them separate
