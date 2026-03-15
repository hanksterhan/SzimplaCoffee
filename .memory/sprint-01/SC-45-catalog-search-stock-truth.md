# SC-45 - Catalog search and stock truth

## What changed

- Added `availability_status` and `availability_label` to product summaries and details.
- Derived summary availability from variant flags and latest-offer availability instead of using product activity as a stock proxy.
- Updated the products catalog search copy to say search is name-only.
- Switched catalog cards and quick-view badges to render the explicit backend availability fields.
- Synced the frontend API schema type file with the summary/detail fields the catalog now uses.

## Why it changed

The products catalog was overstating both search and inventory truth. The UI implied metadata search that the backend does not perform, and it treated `product.is_active` as if it meant a buyable item was in stock. This change makes the search promise narrower and the stock label follow actual variant availability.

## Notes / sharp edges

- Products with no variant rows render `Availability unknown` intentionally. That is more honest than calling them in stock or unavailable.
- Backend verification still depends on the root repo venv (`../.venv/bin/...`) because `backend/.venv` does not contain `pytest` or `ruff`.
- The delivery workflow requested a `stage` base branch, but this repo currently exposes only `main`, so the draft PR targets `main`.

## Verification

- `cd backend && ../.venv/bin/pytest tests/test_api_products.py -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- `cd frontend && npm run build`
