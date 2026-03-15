# SC-48 - Server-side catalog querying

## What changed

- Expanded the products API so search and merchant catalog endpoints accept backend filters for merchant, stock, bean status, sale status, normalized metadata, and price-per-oz bounds.
- Switched products API sorting to backend-owned corpus-wide ordering, with offset-style numeric cursors that remain valid across non-ID sort modes.
- Added endpoint-level product API tests covering server-side filtering and globally truthful sorting behavior.
- Rewired the frontend products query hook and page controls so merchant filters and sort mode are sent to the backend instead of applied only over the loaded pages.
- Synced the frontend API schema typings to the new products query contract.

## Why it changed

The products page was sorting only the currently loaded window, which made rankings like price and discount untrustworthy across the full catalog. This ticket moves ranking truth into the backend and keeps the UI as a query-state client.

## Notes / sharp edges

- The numeric `cursor` for product search now represents a zero-based offset into the sorted result set, not a product ID.
- Backend sorting is intentionally computed after loading the filtered corpus so price-per-oz and sale status can use the same derived summary facts the UI cards display.
- Merchant filter options still key off search text and category, not every possible advanced backend filter.
- The repo still has no `stage` branch, so the delivery PR targets `main`.

## Verification

- `cd backend && ../.venv/bin/pytest tests/test_api_products.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/api/products.py src/szimplacoffee/schemas/products.py tests/test_api_products.py`
- `cd backend && ../.venv/bin/ruff check src tests`
- `cd frontend && npm run build`
- `cd backend && ../.venv/bin/pytest -q`
