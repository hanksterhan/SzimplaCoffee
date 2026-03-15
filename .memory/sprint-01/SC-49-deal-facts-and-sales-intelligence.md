# SC-49 - Deal facts and sales intelligence

## What changed

- Added a `VariantDealFact` model so per-variant historical pricing baselines and discount deltas can be materialized from offer snapshots.
- Upgraded recommendation deal scoring to use historical 7-day and 30-day baselines, compare-at discounts, promo context, and landed price-per-ounce context.
- Added a `build_biggest_sales()` path that filters for quality-clearing whole-bean offers and returns explainable deal candidates.
- Exposed the new `GET /api/v1/recommendations/biggest-sales` endpoint with explicit reason strings for each sale candidate.
- Expanded recommendation tests to cover historical fact generation, history-aware deal scoring, and the biggest-sales API.

## Why it changed

The app could not identify trustworthy deals because it only looked at the latest offer and compare-at hints. This ticket adds the first historical fact layer so sales intelligence can reference recent baselines and explain why a candidate is a real deal.

## Notes / sharp edges

- Historical baselines currently use medians of prior offer snapshots in the trailing 7-day and 30-day windows before the latest offer.
- The new fact rows are materialized from existing offer history, so stronger deal quality still depends on SC-50 increasing the amount and cadence of snapshot collection over time.
- The biggest-sales endpoint only returns whole-bean, available, quality-clearing offers.
- The repo still has no `stage` branch, so the delivery PR targets `main`.

## Verification

- `cd backend && ../.venv/bin/pytest tests/test_recommendations.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/services/recommendations.py src/szimplacoffee/api/recommendations.py src/szimplacoffee/models.py tests/test_recommendations.py`
- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
