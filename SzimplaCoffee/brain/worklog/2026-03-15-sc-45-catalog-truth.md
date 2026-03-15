# 2026-03-15 - SC-45 catalog search and stock truth

Completed SC-45 delivery work:

- added explicit availability fields to product summaries and details
- derived catalog stock truth from variant and latest-offer availability instead of `product.is_active`
- updated the products page copy so search promises only name matching
- switched products grid and quick-view badges to render the new availability fields
- synced the frontend API schema type file for the fields the catalog now reads

Verification completed:

- `cd backend && ../.venv/bin/pytest tests/test_api_products.py -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- `cd frontend && npm run build`
- draft PR opened at `https://github.com/hanksterhan/SzimplaCoffee/pull/2`
