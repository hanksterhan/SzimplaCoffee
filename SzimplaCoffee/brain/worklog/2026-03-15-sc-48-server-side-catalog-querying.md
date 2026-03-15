# 2026-03-15 - SC-48 server-side catalog querying

Completed SC-48 delivery work:

- moved product search sorting and shopping-relevant filtering into the backend
- added server-side query params for merchant, stock, whole-bean status, sale state, normalized metadata, and price-per-oz bounds
- switched product pagination to a sorted-result offset cursor so non-ID sort modes stay truthful across pages
- rewired the frontend products page to send merchant and sort state to the backend instead of sorting locally
- expanded product API tests to cover endpoint filtering and global sorting behavior

Verification completed:

- `cd backend && ../.venv/bin/pytest tests/test_api_products.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/api/products.py src/szimplacoffee/schemas/products.py tests/test_api_products.py`
- `cd backend && ../.venv/bin/ruff check src tests`
- `cd frontend && npm run build`
- `cd backend && ../.venv/bin/pytest -q`
- draft PR opened at `https://github.com/hanksterhan/SzimplaCoffee/pull/5`
