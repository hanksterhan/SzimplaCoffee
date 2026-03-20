# SC-108: Server-side catalog sort

**Delivered:** 2026-03-20T10:45:00Z

## What changed

- Added `/api/v1/products/catalog` endpoint — corpus-wide product browsing with `sort` query param and `quality` as default sort.
- Added `freshness` sort variant to `ProductSort` literal (schemas + frontend hook).
- `_sort_results()` already handled `quality`, `price_*`, `discount`, and `merchant` — we added the `freshness` branch (order by `last_seen_at` desc).
- Frontend `/products` page: default sort changed from `"featured"` → `"quality"`. Added `"Freshness: newest first"` option. Improved dropdown label display.
- New test file: `backend/tests/test_catalog_sort.py` — 6 tests covering quality order, price_low, price_high, default==quality, freshness, and cursor pagination.

## Why

Phase 2 goal: catalog semantics should reflect normalized metadata and trustworthy ordering. With 36 merchants, default insertion-order sort made the catalog meaningless. Quality-first sort immediately surfaces high-trust merchants.

## Verification

- 333 backend tests pass (6 new)
- ruff clean
- frontend `npm run build && npx tsc -b` clean

## Surprises

- The sort infrastructure and frontend dropdown already existed for `quality`, `price_*`, etc. — ticket underestimated how much was already there. The real work was:
  1. Adding the `/products/catalog` endpoint (distinct from `/products/search`)
  2. Adding `freshness` sort
  3. Changing the default from `featured` to `quality`
  4. Writing the test file

## Notes for next runs

- The product catalog now has a proper quality-first default. Phase 2 success criteria are substantially met.
- Backlog is empty (0 open tickets). Next run should trigger `create-tickets` to refill from brainstorm.
- `completed_since_reflect` will hit 7 — reflection is overdue (threshold=5). Next run should trigger reflect.
- Brainstorm packet may need refresh for Phase 3 tickets.
