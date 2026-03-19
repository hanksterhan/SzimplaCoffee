# 2026-03-18 - SC-72 brew feedback ranking

Completed SC-72 closeout work:

- added brew-feedback aggregation to recommendation scoring
- introduced configurable threshold and penalty constants for low-rated coffees
- kept unrated coffees neutral so missing data does not act as a penalty
- added focused backend tests for neutral, above-threshold, and below-threshold brew feedback cases

Verification completed:

- `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -v -k brew`
- `cd backend && ~/.local/bin/ruff check src/szimplacoffee/services/recommendations.py tests/test_recommendations.py`
