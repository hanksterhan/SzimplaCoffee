# SC-57 Execution Plan

## Goal
Verify and bulk-import at least 15 merchants from the top-500-seed.md brain file into the merchant registry with appropriate tier assignments.

## Context
The merchant registry is sparse. The seed file at `SzimplaCoffee/brain/merchants/top-500-seed.md` contains candidate URLs for specialty coffee roasters. Before importing, URLs must be verified as live.

## Files / Areas Expected to Change
- `SzimplaCoffee/brain/merchants/top-500-seed.md` (read-only reference)
- `backend/src/szimplacoffee/bootstrap.py` (may add seed imports)
- `backend/src/szimplacoffee/cli.py` (invoke add-merchant per URL)

## Implementation Steps
1. Read `SzimplaCoffee/brain/merchants/top-500-seed.md` and extract candidate URLs
2. Select top 15-20 by recognizability (known specialty roasters with likely Shopify/WooCommerce storefronts)
3. HTTP GET check each URL — skip any that return non-2xx or timeout
4. For each verified URL: `cd backend && . .venv/bin/activate && szimpla add-merchant <url>`
5. After import: `szimpla score-merchants` to initialize quality profiles
6. Confirm merchants table row count >= 15
7. Confirm all have trust_tier and crawl_tier set

## Risks / Notes
- Some seed URLs may be outdated or redirect to dead pages
- `add-merchant` may fail on unusual URL formats — handle gracefully
- Set trust_tier=C, crawl_tier=B as default for all new imports
- Well-known Shopify roasters (Blue Bottle, Stumptown, Intelligentsia) are good starting points

## Verification
```bash
cd backend && python -c "
from szimplacoffee.db import engine
from sqlalchemy import text
conn = engine.connect()
total = conn.execute(text('SELECT COUNT(*) FROM merchants')).scalar()
no_tier = conn.execute(text('SELECT COUNT(*) FROM merchants WHERE trust_tier IS NULL')).scalar()
print(f'Total merchants: {total}, Missing tier: {no_tier}')
"
curl -s http://localhost:8000/api/v1/merchants | python -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('merchants', d) if isinstance(d,dict) else d))"
```

## Out of Scope
- Crawling the merchants (SC-58)
- Bulk import CLI command (SC-59)
- Trust promotion after crawls (SC-60)
