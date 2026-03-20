# SC-99 Delivery Memory — Quality Sort Mode

**Date:** 2026-03-20
**Branch:** feat/SC-99-quality-sort → merged to stage
**Status:** Done

## What Changed

- `backend/src/szimplacoffee/schemas/products.py`: Added `"quality"` to `ProductSort` Literal.
- `backend/src/szimplacoffee/api/products.py`:
  - Added quality sort branch in `_sort_results`: `has_stock desc → merchant_quality_score desc → metadata_confidence desc → last_seen_at desc`.
  - Added `merchant_quality_score: float = 0.5` field to `ProductResultRow` dataclass.
  - Extended `_build_product_result` to accept and store `merchant_quality_score`.
  - Merchant products endpoint: switched from `db.get()` to `db.scalars(select(...).options(selectinload(Merchant.quality_profile)))` to eager-load quality profile.
  - Search endpoint: added `selectinload(Merchant.quality_profile)` to batch merchant load; computed `merchant_quality_scores` dict from profiles.
- `backend/tests/test_api_products.py`:
  - Added `MerchantQualityProfile` import.
  - Added `quality_sort_client` fixture: 2 merchants with different `MerchantQualityProfile.overall_quality_score` values (0.9 / 0.3), 3 products (2 in-stock, 1 sold-out).
  - Added `test_quality_sort_orders_by_stock_then_merchant_quality_then_confidence`: verifies in-stock HQ first, in-stock LQ second, sold-out last.
- `frontend/src/api/schema.d.ts`: Added `"quality"` to sort literal union in both search and catalog endpoint parameter types.
- `frontend/src/routes/products.lazy.tsx`: Added `["quality", "Quality: best first"]` to sort selector options list.

## Key Discovery

`overall_quality_score` is on `MerchantQualityProfile`, not `Merchant` directly. The plan referenced `Merchant.overall_quality_score` which doesn't exist. Fixed by:
1. Using `merchant.quality_profile.overall_quality_score` with null-safe fallback to 0.5.
2. Adding `selectinload(Merchant.quality_profile)` to avoid lazy-load N+1.

## Verification

- 275 backend tests pass (was 274 before SC-99, +1 new test).
- Frontend build clean (vite build + tsc -b).
- Feature branch merged to stage and pushed.

## Follow-ups

- SC-100: Today view deal badge wiring (ready).
- SC-101: Merchant expansion via CLI (ready).
- "quality" sort is not the default — `featured` remains default. Could switch later once user feedback is gathered.
