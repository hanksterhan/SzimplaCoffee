# SC-98 Execution Plan — Expose deal baselines in catalog API and Today view

## Goal

Surface `VariantDealFact` deal signals (30-day baseline, price drop %, compare_at discount)
in the catalog API response and show a lightweight badge in `ProductCard` when a meaningful
deal signal is present (price_drop_30d_percent > 5%).

## Context

- `VariantDealFact` rows are already computed post-crawl by
  `materialize_variant_deal_facts` in `services/recommendations.py`.
- The model has: `baseline_30d_cents`, `price_drop_30d_percent`,
  `compare_at_discount_percent`, `historical_low_cents`, `historical_high_cents`.
- Currently these are only used inside the recommendation engine; they are not
  exposed in any API response.
- `ProductSummary` schema is the primary response shape for catalog list endpoints.
- The catalog query in `api/products.py` already fetches `ProductVariant` rows;
  deal_fact is a `uselist=False` relationship on `ProductVariant`, so it can be
  eagerly loaded without extra queries.

## Files Expected to Change

**Backend:**
- `backend/src/szimplacoffee/schemas/products.py` — add nullable deal_fact fields
- `backend/src/szimplacoffee/api/products.py` — populate deal_fact in catalog query
- `backend/tests/test_api_products.py` — add deal_fact API test

**Frontend:**
- `frontend/src/api/schema.d.ts` — regenerate after schema change (via `npm run gen:api`)
- `frontend/src/components/ProductCard.tsx` — deal badge
- `frontend/src/components/ProductQuickView.tsx` — optional deal detail line

## Implementation Steps

### S1 — Backend schema + endpoint

1. Read `schemas/products.py` to understand current `ProductSummary` and variant fields.
2. Add a `DealFactSchema` (or inline optional fields) to `ProductSummary`:
   ```python
   class DealFactSchema(BaseModel):
       baseline_30d_cents: int | None = None
       price_drop_30d_percent: float | None = None
       compare_at_discount_percent: float | None = None
       historical_low_cents: int | None = None
   ```
3. Add `deal_fact: DealFactSchema | None = None` to `ProductSummary`.
4. In `api/products.py`, find where `ProductResultRow` / `ProductSummary` is assembled
   from query results. Add eager loading for `variant.deal_fact` (check if
   `selectinload` or `joinedload` is already used on variants; add deal_fact there).
5. Populate `summary.deal_fact` from the loaded relationship when present.
6. Add a test: create a `VariantDealFact` row in the test DB, call catalog endpoint,
   assert deal_fact fields are present and correct.

### S2 — Frontend badge

1. Start the backend before running `gen:api` (it hits localhost:8000/openapi.json at runtime):
   ```bash
   cd backend && uvicorn szimplacoffee.main:app --port 8000 &
   sleep 3   # wait for startup
   ```
2. Run `cd frontend && npm run gen:api` after backend is updated (backend must be running).
2. In `ProductCard.tsx`, read the deal_fact field from the product summary.
3. Add a badge: if `deal_fact.price_drop_30d_percent > 5`, show
   "↓{n}% vs 30d avg" (round to integer).
4. If `deal_fact.compare_at_discount_percent > 0` and no 30d signal, show
   "Save {n}%" instead.
5. When deal_fact is null/absent, render nothing.
6. Optional: add a line in `ProductQuickView.tsx` showing "30-day avg: $X.XX".
7. Run `npm run build` and `npx tsc -b`.

## Risks / Notes

- Eager loading: confirm that adding `selectinload(ProductVariant.deal_fact)` in the
  catalog query doesn't cause a regression. Use `EXPLAIN QUERY PLAN` or check test
  timing if unsure.
- Not all variants will have a `VariantDealFact` row (new products, no history).
  Always null-guard.
- Badge copy should be consistent with existing badge styles in ProductCard.
- Do not display confusing signals (e.g. both compare_at and 30d drop at the same time);
  prefer the more meaningful one.

## Verification

```bash
cd backend && .venv/bin/pytest tests/ -q
cd frontend && npm run build
cd frontend && npx tsc -b
```

## Out of Scope

- Recommendation engine changes
- Historical price chart
- Backfilling VariantDealFact rows (already runs post-crawl)
