# SC-74 Execution Plan

## Goal
Add crawl health fields to the merchant API — backend only.

## Context
Watch page UI rendering is SC-79. Split to keep each cycle focused.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/schemas/merchants.py`
- `backend/src/szimplacoffee/api/merchants.py`

## Implementation Steps
1. Add last_crawl_at, crawl_success, product_count, metadata_pct to MerchantSummary schema
2. Update merchant list query to JOIN crawl_runs (latest per merchant) and COUNT products
3. Compute metadata_pct as (products with origin OR process OR roast_level) / total * 100
4. Run npm run gen:api to regenerate frontend types
5. Add pytest coverage

## Verification
- `cd backend && .venv/bin/pytest tests/ -q`
- `cd backend && .venv/bin/ruff check src/ tests/`
- `cd frontend && npm run gen:api && npm run build`

## Out of Scope
- Watch page UI (SC-79)
