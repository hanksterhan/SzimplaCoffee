# SC-68 Execution Plan

## Goal
Confirm or establish that VariantDealFact rows are created automatically after each successful crawl. Verify the table is populated after crawl-all.

## Context
The recommendation engine likely joins on variant_deal_facts to rank products by deal quality. If this table is empty, no candidates survive the join and recommendations return empty. This ticket closes that gap.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/crawlers.py` (add post-crawl hook if missing)
- `backend/src/szimplacoffee/services/recommendations.py` (verify join usage)

## Implementation Steps
1. Inspect models.py to confirm VariantDealFact model and table exist
2. Check variant_deal_facts table exists and current row count:
   ```bash
   cd backend && python -c "
   from szimplacoffee.db import engine
   from sqlalchemy import text
   print(engine.connect().execute(text('SELECT COUNT(*) FROM variant_deal_facts')).scalar())
   "
   ```
3. Search crawlers.py for deal fact computation calls:
   ```bash
   grep -n "deal_fact\|VariantDealFact\|compute_deal" backend/src/szimplacoffee/services/crawlers.py
   ```
4. Search recommendations.py for deal fact join:
   ```bash
   grep -n "deal_fact\|VariantDealFact" backend/src/szimplacoffee/services/recommendations.py
   ```
5. If deal fact computation is not called post-crawl, add it:
   - Find the post-crawl success callback in crawlers.py
   - Call the existing deal fact compute function (do not reimplement)
6. Run crawl-all and verify table populates:
   ```bash
   cd backend && . .venv/bin/activate && szimpla crawl-all
   python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM variant_deal_facts')).scalar())"
   ```

## Risks / Notes
- If the table schema doesn't exist, run alembic revision --autogenerate first
- Do not change deal fact computation algorithm — only wire it into the crawl hook

## Verification
```bash
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM variant_deal_facts')).scalar())"
grep -n "deal_fact\|VariantDealFact" backend/src/szimplacoffee/services/crawlers.py
cd backend && ruff check src/ tests/ && pytest tests/ -v
```

## Out of Scope
- Changing deal fact computation algorithm
- Backfilling historical data
- Frontend changes
