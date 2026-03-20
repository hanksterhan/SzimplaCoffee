# SC-107 Execution Plan

## Goal

Add historical price baselines per variant to support deal-scoring in the recommendation engine and Today view. A new VariantPriceBaseline model stores median/min/max price over a 90-day window, computed from existing OfferSnapshot data.

## Context

SC-105 expanded the merchant set to 36 active merchants with ~290+ products and thousands of offer snapshots. The data is there to compute baselines. This ticket builds the computation layer and exposes it via the API so SC-109 can use it for deal-scoring.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/models.py` — add VariantPriceBaseline model
- `backend/migrations/versions/<hash>_add_variant_price_baseline.py` — Alembic migration
- `backend/src/szimplacoffee/services/baseline_service.py` — new service
- `backend/src/szimplacoffee/cli.py` — add `compute-baselines` command
- `backend/src/szimplacoffee/schemas/products.py` — add baseline fields to ProductDetailResponse
- `backend/src/szimplacoffee/api/products.py` — join baseline in product detail endpoint
- `backend/tests/test_baseline_service.py` — unit tests

## Implementation Steps

1. **Read models.py** to understand current ProductVariant and OfferSnapshot structure.
2. **Add VariantPriceBaseline model**: table with variant_id (FK, unique), median_price, min_price, max_price, sample_count, baseline_window_days (int, default 90), computed_at (DateTime).
3. **Generate Alembic migration**: `cd backend && alembic revision --autogenerate -m "add_variant_price_baseline"`. Review and adjust if needed.
4. **Write baseline_service.py**: `compute_variant_baselines(db, merchant_id=None, window_days=90)`. Query OfferSnapshot grouped by variant_id, filter to last `window_days` days, compute median (use Python statistics.median), min, max, count. Upsert VariantPriceBaseline rows.
5. **Add CLI command**: `szimpla compute-baselines [--merchant-id N]` that calls the service.
6. **Update ProductDetailResponse schema**: add optional `baseline_price`, `baseline_min_price`, `baseline_max_price`, `baseline_sample_count` fields (all Optional[float/int]).
7. **Update product detail endpoint**: left-join VariantPriceBaseline when building the response.
8. **Write tests**: test_baseline_service.py covering empty history, single snapshot, multi-snapshot median, 90-day window cutoff.
9. **Run verification**: `pytest tests/ -q`, `alembic upgrade head`, `ruff check src/ tests/`.

## Risks / Notes

- OfferSnapshot may have sparse data for newer merchants — baseline computation should handle empty results gracefully (no rows created, not an error).
- Use `statistics.median()` from Python stdlib — no numpy dependency needed.
- Migration must be safe to run on a live DB (adds a new table, no destructive changes).
- Baseline computation may be slow for large history — use a single SQL query with GROUP BY rather than loading all rows into Python.

## Verification

1. `cd backend && alembic upgrade head` — migration applies cleanly
2. `cd backend && . .venv/bin/activate && szimpla compute-baselines` — runs without error
3. `cd backend && pytest tests/ -q` — all tests pass
4. `cd backend && ~/.local/bin/ruff check src/ tests/` — no lint errors

## Out of Scope

- Frontend deal badge UI (SC-109)
- Recommendation engine integration (SC-109)
- Subscription deal handling
- Price trend charts
