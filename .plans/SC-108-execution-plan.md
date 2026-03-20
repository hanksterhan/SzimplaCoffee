# SC-108 Execution Plan

## Goal

Add a `sort` parameter to the product catalog endpoint and a sort selector to the frontend catalog page, enabling quality-first and freshness-aware corpus-wide product ordering.

## Context

With 36 active merchants and 290+ products, the catalog currently has no meaningful default sort. Adding a quality-first sort makes the browse experience immediately more useful. This is a targeted backend + frontend change with minimal risk.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/api/products.py` — add sort query param, implement sort logic
- `backend/src/szimplacoffee/schemas/products.py` — possibly extend catalog query schema
- `backend/tests/test_catalog_sort.py` — new test file
- `frontend/src/routes/products.lazy.tsx` — add sort selector UI, pass sortBy state
- `frontend/src/hooks/use-products.ts` — pass sort param to API call

## Implementation Steps

1. **Read products.py (backend)**: understand current catalog query structure and how MerchantQualityProfile is joined (if at all).
2. **Add sort param**: `sort: str = Query("quality", enum=["quality", "freshness", "price_asc", "price_desc"])`.
3. **Implement quality sort**: join `MerchantQualityProfile.overall_score` via merchant_id. `ORDER BY overall_score DESC NULLS LAST, merchant.last_crawled_at DESC`.
4. **Implement freshness sort**: `ORDER BY merchant.last_crawled_at DESC NULLS LAST`.
5. **Implement price sorts**: `ORDER BY current_price ASC/DESC` via VariantDealFact join (already present in catalog query, verify).
6. **Write test_catalog_sort.py**: create test merchants with different quality scores, verify sort=quality returns them in descending score order.
7. **Read products.lazy.tsx and use-products.ts** to understand current filter/state pattern.
8. **Add sortBy state** to catalog page (default "quality"). Render `<Select>` with options: Quality, Freshness, Price: Low to High, Price: High to Low.
9. **Update useProducts hook**: accept and pass `sort` query param to API.
10. **Run build + typecheck**: `npm run build && npx tsc -b`.
11. **Verify backend tests**: `pytest tests/ -q`.

## Risks / Notes

- MerchantQualityProfile may not be joined in the current catalog query — check and add the join efficiently (avoid N+1).
- Default sort=quality means the existing catalog response order will change — this is intentional and expected.
- Keep the sort selector simple (no animations, no complex state) to keep diff minimal.

## Verification

1. `cd backend && pytest tests/ -q`
2. `cd frontend && npm run build && npx tsc -b`
3. `cd backend && ~/.local/bin/ruff check src/ tests/`
4. Manual: open /products, confirm sort selector visible and switching reorders list.

## Out of Scope

- Recommendation engine sort changes
- Search endpoint sort
- Today view ranking changes
- Mobile-specific sort UI
