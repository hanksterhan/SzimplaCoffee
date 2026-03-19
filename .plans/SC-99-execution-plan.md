# SC-99 Execution Plan — Add quality-first server-side product sort mode

## Goal

Add a "quality" sort mode to the catalog API that orders products by:
in-stock first → merchant quality score → metadata_confidence → recency.
Expose it as an option in the frontend sort selector.

## Context

- `ProductSort` is a `Literal` type in `schemas/products.py`.
- `_sort_results` in `api/products.py` dispatches on the sort value.
- The default "featured" sort already ranks by `has_stock`, `metadata_confidence`,
  and `last_seen_at`. The new "quality" sort adds merchant quality as a primary signal.
- `Merchant.overall_quality_score` and `MerchantQualityProfile.overall_quality_score`
  exist; prefer the denormalized field on `Merchant` to avoid an extra join.
- `ProductResultRow` is a dataclass in `api/products.py` — check its current fields
  before deciding whether to add `merchant_quality_score` to it.

## Files Expected to Change

**Backend:**
- `backend/src/szimplacoffee/schemas/products.py` — add "quality" to ProductSort
- `backend/src/szimplacoffee/api/products.py` — add quality sort branch; ensure merchant quality is available in ProductResultRow
- `backend/tests/test_api_products.py` — test quality sort ordering

**Frontend:**
- `frontend/src/api/schema.d.ts` — regenerate after schema change
- `frontend/src/routes/products.lazy.tsx` — add "Quality" option to sort selector

## Implementation Steps

### S1 — Backend

1. Read `schemas/products.py` to see current ProductSort Literal.
2. Add `"quality"` to the Literal.
3. Read `ProductResultRow` dataclass in `api/products.py` to see current fields.
4. Check if `merchant_quality_score` (or equivalent) is already present.
   - If not: add `merchant_quality_score: float` to `ProductResultRow`; populate it
     in the catalog query from `Merchant.overall_quality_score`.
   - The catalog query already joins Merchant to fetch `merchant_name`; extend that
     join to also select `Merchant.overall_quality_score`.
5. Add "quality" branch to `_sort_results`:
   ```python
   if sort == "quality":
       return sorted(rows, key=lambda row: (
           -int(row.has_stock),
           -(row.merchant_quality_score or 0.0),
           -row.summary.metadata_confidence,
           -row.summary.last_seen_at.timestamp(),
           row.summary.merchant_name.lower(),
           row.summary.id,
       ))
   ```
6. Write test: create 2 merchants with different `overall_quality_score` values,
   add products for each, call `GET /products/catalog?sort=quality`, assert ordering.

### S2 — Frontend

1. Regenerate `schema.d.ts` (backend must be running): `npm run gen:api`.
2. In `products.lazy.tsx`, find the sort selector options array.
3. Add `{ value: "quality", label: "Quality" }` to the options.
4. Build and type-check: `npm run build && npx tsc -b`.

## Risks / Notes

- Python-level sort is fine for the current corpus (918 products). No SQL ORDER BY
  migration needed unless the corpus grows significantly.
- If `ProductResultRow` does not yet carry `merchant_quality_score`, adding it requires
  touching the catalog query SELECT or row assembly. Be careful not to break existing
  sort modes.
- `Merchant.overall_quality_score` defaults to 0.5; sort should handle this gracefully.

## Verification

```bash
cd backend && .venv/bin/pytest tests/test_api_products.py -v -k 'quality'
cd backend && .venv/bin/pytest tests/ -q
cd frontend && npm run build
cd frontend && npx tsc -b
```

## Out of Scope

- Making quality the default sort
- SQL ORDER BY migration
- Recommendation engine changes
