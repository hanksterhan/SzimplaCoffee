# SC-98 — Expose deal baselines in catalog API

**Date:** 2026-03-20
**Commit:** a8bebc1
**Branch:** stage (direct commit, no feature branch needed since scope was clean)

## What changed

- Added `DealFactSchema` to `schemas/products.py` with 4 nullable fields:
  `baseline_30d_cents`, `price_drop_30d_percent`, `compare_at_discount_percent`,
  `historical_low_cents`
- Added `deal_fact: Optional[DealFactSchema] = None` to `ProductSummary`
- Updated both catalog query selectinloads (merchant-products + global search) to also
  eagerly load `ProductVariant.deal_fact` — avoids N+1 queries
- Added `_deal_fact_schema_from_variant` helper; called from `_product_summary_with_merchant`
- Also updated `/products/{id}` detail endpoint selectinload
- Frontend: regenerated `schema.d.ts`, added `DealBadge` component in `products.lazy.tsx`
  showing `↓N% vs 30d avg` when `price_drop_30d_percent > 5`, or `Save N%` for
  compare_at signal; badge shown in both ProductCard overlay and ProductQuickView price row
- 4 new backend tests; 274/274 passing; frontend build + tsc clean

## Key decisions

- Chose selectinload (not joinedload) for deal_fact to match the existing offers loading pattern
- Null-guarded at schema level — `price_drop_30d_percent=0.0` and `historical_low_cents=0`
  are treated as absent (falsy) to avoid displaying zero-value badges
- DealBadge positions: ProductCard image overlay (below espresso badge if both present);
  ProductQuickView inline with price row
- Threshold for "meaningful deal": price_drop_30d_percent > 5% (same as ticket AC-2)

## Surprises

- `ProductCard` and `ProductQuickView` are inline in `products.lazy.tsx`, not separate files —
  the ticket description listed separate component files that don't exist yet
- The existing `ProductCardSummary` type already extended `ProductSummary`; just added
  `deal_fact` to it

## Follow-ups

- SC-99 (quality sort) is still ready — purely backend-only, safe next task
- When enough VariantDealFact rows exist in prod DB, badges will appear automatically
- Could eventually promote deal sort / deal filter to a dedicated endpoint filter
