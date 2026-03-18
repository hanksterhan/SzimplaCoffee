# SC-72 — Brew feedback penalty in recommendation ranking

## What changed
- Added `BREW_PENALTY_THRESHOLD = 3.0` and `BREW_PENALTY_WEIGHT = 0.15` to the recommendation service.
- Aggregated average `BrewFeedback.rating` by `product_id` during recommendation building.
- Applied the penalty only when a product has feedback and its average rating falls below the threshold.
- Extended recommendation tests to cover no-feedback, above-threshold, and below-threshold behavior.

## Why it changed
SzimplaCoffee already records brew feedback, but the recommendation engine treated badly performing coffees the same as unrated coffees. This ticket closes that loop so weak repeat brews become a real ranking signal without turning lack of data into a negative signal.

## Verification
- `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -v -k brew`
- `cd backend && ~/.local/bin/ruff check src/szimplacoffee/services/recommendations.py tests/test_recommendations.py`
- `cd backend && grep -n "BREW_PENALTY" src/szimplacoffee/services/recommendations.py`

## Notes / sharp edges
- The penalty currently acts as a flat score deduction instead of a scaled penalty curve.
- `score_breakdown` now includes `brew_avg_rating` and `brew_penalty`, which should help future recommendation debugging.
