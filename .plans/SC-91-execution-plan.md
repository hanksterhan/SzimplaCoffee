# SC-91 Execution Plan

## Goal

Add Ritual Coffee Roasters as the 15th trusted merchant to reach the goal criterion `merchants_15_plus=True`.

## Context

Current state: 14 Tier A active trusted merchants. Goal requires 15+. Ritual Coffee Roasters (`ritualroasters.com`) is a known high-quality SF specialty roaster listed in `SzimplaCoffee/brain/merchants/top-500-seed.md` as Tier A, Shopify platform. The `szimpla add-merchant` CLI handles platform detection and merchant creation.

No code changes are expected — this is a data import task using existing CLI.

## Files / Areas Expected to Change

**No source code changes expected.** This is a CLI/data operation.

- DB: `data/szimplacoffee.db` — new merchant row, crawl run row, product rows
- Potentially: `backend/src/szimplacoffee/bootstrap.py` if we need to persist the promotion logic

## Implementation Steps

### Step 1 — Add merchant via CLI

```bash
cd backend
. .venv/bin/activate
szimpla add-merchant https://ritualroasters.com --crawl-now
```

Expected output: `Added merchant Ritual Coffee Roasters (shopify)`

If `--crawl-now` is not available, run separately:
```bash
szimpla add-merchant https://ritualroasters.com
szimpla crawl-all
```

### Step 2 — Verify merchant was created

```bash
cd backend && .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from szimplacoffee.db import engine
from sqlalchemy import text
with engine.connect() as c:
    row = c.execute(text(\"SELECT id,name,crawl_tier,trust_tier,is_active FROM merchants WHERE name LIKE '%Ritual%'\")).fetchone()
    print(row)
"
```

### Step 3 — Promote to Tier A and trust_tier=trusted if needed

If crawl_tier != 'A' or trust_tier != 'trusted':

```bash
cd backend && .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from szimplacoffee.db import engine, session_scope
from sqlalchemy import text
with session_scope() as session:
    m = session.execute(text(\"SELECT id FROM merchants WHERE name LIKE '%Ritual%'\")).fetchone()
    if m:
        session.execute(text(\"UPDATE merchants SET crawl_tier='A', trust_tier='trusted' WHERE id=:id\"), {'id': m[0]})
        print(f'Promoted merchant id={m[0]}')
"
```

### Step 4 — Verify products crawled

```bash
cd backend && .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from szimplacoffee.db import engine
from sqlalchemy import text
with engine.connect() as c:
    n = c.execute(text(\"SELECT COUNT(*) FROM products p JOIN merchants m ON p.merchant_id=m.id WHERE m.name LIKE '%Ritual%'\")).scalar()
    print(f'Ritual products: {n}')
"
```

If 0 products, the crawl may have failed. Check crawl_runs table:
```bash
cd backend && .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from szimplacoffee.db import engine
from sqlalchemy import text
with engine.connect() as c:
    rows = c.execute(text(\"SELECT id, merchant_id, started_at, status, error_message FROM crawl_runs ORDER BY id DESC LIMIT 5\")).fetchall()
    for r in rows: print(r)
"
```

If crawl failed, try:
```bash
cd backend && szimpla crawl-all
```

### Step 5 — Run backfill-metadata on new products

```bash
cd backend && szimpla backfill-metadata
```

This re-runs the coffee parser on all products, filling in origin, process, roast, and variety for Ritual products.

### Step 6 — Verify goal criterion flipped

```bash
cd backend && .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from szimplacoffee.db import engine
from sqlalchemy import text
with engine.connect() as c:
    n = c.execute(text(\"SELECT COUNT(*) FROM merchants WHERE trust_tier='trusted' AND is_active=1\")).scalar()
    print(f'Trusted merchants: {n} (goal: 15)')
    assert n >= 15, f'Only {n} trusted merchants'
"
```

### Step 7 — Run backend tests

```bash
cd backend && .venv/bin/pytest tests/ -q
```

## Risks / Notes

- **Crawl may fail**: Ritual's website may have changed structure. If Shopify adapter fails, check crawl_runs for error_message. If crawl returns 0 products, try re-running szimpla crawl-all.
- **Platform detection**: If `detect_platform` returns 'unknown', crawl_tier may default to C. Manually promote after checking the platform.
- **session_scope import**: Check if it's exported from `szimplacoffee.db` or needs adjustment.
- **No source code changes** unless CLI has a bug that needs fixing.

## Verification

1. `SELECT COUNT(*) FROM merchants WHERE trust_tier='trusted' AND is_active=1` → ≥ 15
2. `SELECT COUNT(*) FROM products p JOIN merchants m ON p.merchant_id=m.id WHERE m.name LIKE '%Ritual%'` → ≥ 5
3. `pytest tests/ -q` → all green

## Out of Scope

- Adding multiple merchants in this ticket
- Changes to crawl strategy or adapters
- Frontend changes
