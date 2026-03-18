# SC-61 Execution Plan

## Goal
Audit whether coffee_parser.py is wired into the post-crawl pipeline. Measure baseline fill rates for origin, process, roast_level, and variety. Run backfill-metadata and document improvement.

## Context
Sprint 2 data showed only 59/910 products have origin and 43/910 have process. It is unknown whether this is a wiring gap (parser not running) or a pattern quality gap. This ticket determines which.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/coffee_parser.py` (read, possibly add scheduler call)
- `backend/src/szimplacoffee/scheduler.py` (confirm or add post-crawl hook)
- `backend/src/szimplacoffee/services/crawlers.py` (confirm post-crawl call)

## Implementation Steps
1. Read coffee_parser.py — understand what fields it populates and what it returns
2. Search for coffee_parser calls in scheduler.py and crawlers.py:
   ```bash
   grep -rn "coffee_parser\|parse_coffee\|backfill" backend/src/szimplacoffee/
   ```
3. If not wired: add call in crawlers.py post-crawl success handler
4. Measure baseline fill rates:
   ```bash
   cd backend && python -c "
   from szimplacoffee.db import engine
   from sqlalchemy import text
   conn = engine.connect()
   total = conn.execute(text('SELECT COUNT(*) FROM products')).scalar()
   for field in ['origin', 'process', 'roast_level', 'variety']:
       filled = conn.execute(text(f'SELECT COUNT(*) FROM products WHERE {field} IS NOT NULL')).scalar()
       print(f'{field}: {filled}/{total} = {filled/total*100:.1f}%')
   "
   ```
5. Run backfill-metadata:
   ```bash
   cd backend && . .venv/bin/activate && szimpla backfill-metadata 2>&1
   ```
6. Measure post-backfill fill rates and document delta

## Risks / Notes
- backfill-metadata may not exist as CLI command — check cli.py and add if missing
- Wiring the parser correctly is more impactful than regex improvements alone

## Verification
```bash
grep -n "coffee_parser\|parse_coffee" backend/src/szimplacoffee/services/crawlers.py backend/src/szimplacoffee/scheduler.py
cd backend && . .venv/bin/activate && szimpla backfill-metadata 2>&1 | tail -10
```

## Out of Scope
- Improving regex patterns (SC-62, SC-63)
- Dashboard metric changes (SC-64)
