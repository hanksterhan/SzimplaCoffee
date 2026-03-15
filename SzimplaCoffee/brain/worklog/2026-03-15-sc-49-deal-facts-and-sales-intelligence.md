# 2026-03-15 - SC-49 deal facts and sales intelligence

Completed SC-49 delivery work:

- added a per-variant historical deal fact model sourced from offer snapshot history
- upgraded recommendation deal scoring to use 7-day and 30-day baselines, compare-at signals, promo context, and landed price-per-ounce context
- added a biggest-sales service path and API endpoint with explainable reason strings
- expanded backend tests to cover fact materialization, deal scoring behavior, and the biggest-sales endpoint

Verification completed:

- `cd backend && ../.venv/bin/pytest tests/test_recommendations.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/services/recommendations.py src/szimplacoffee/api/recommendations.py src/szimplacoffee/models.py tests/test_recommendations.py`
- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- draft PR opened at `https://github.com/hanksterhan/SzimplaCoffee/pull/6`
