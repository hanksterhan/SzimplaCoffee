# SC-58 Execution Plan

## Goal
Run crawls on all newly imported merchants and verify that product data is ingested. Document crawl success/failure per merchant.

## Context
After SC-57 imports 15+ merchants, this ticket exercises the full crawl pipeline. The goal is to establish a baseline product count and identify which merchants need adapter fixes.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/crawlers.py` (read for diagnosis)
- `backend/tests/` (add baseline assertion test if helpful)

## Implementation Steps
1. Record pre-crawl product count:
   ```bash
   cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM products')).scalar())"
   ```
2. Run crawl-all:
   ```bash
   cd backend && . .venv/bin/activate && szimpla crawl-all 2>&1 | tee /tmp/crawl-all.log
   ```
3. Record post-crawl product count
4. Query crawl_runs for per-merchant outcomes:
   ```bash
   cd backend && python -c "
   from szimplacoffee.db import engine
   from sqlalchemy import text
   rows = engine.connect().execute(text('SELECT merchant_id, status, COUNT(*) as n FROM crawl_runs GROUP BY merchant_id, status ORDER BY merchant_id')).fetchall()
   for r in rows: print(r)
   "
   ```
5. List merchants with zero products
6. Document results in delivery memory

## Risks / Notes
- Some adapters may fail for merchants on platforms not yet supported
- crawl-all may take several minutes; run with sufficient timeout
- Failures are expected — goal is documentation, not 100% success

## Verification
```bash
# product count grew
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM products')).scalar())"

# crawl_runs populated
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(DISTINCT merchant_id) FROM crawl_runs')).scalar())"
```

## Out of Scope
- Fixing broken adapters
- Metadata parsing
- Trust tier promotion (SC-60)
