# SC-86 Execution Plan

## Goal
Seed 5 additional purchase records so purchase_history has ≥10 rows. At least 3 of the new purchases should reference an existing recommendation_run_id.

## Context
Currently 5 purchases in DB. Goal requires ≥10. The purchase model (PurchaseHistory) is confirmed working from SC-69. The API POST /api/v1/history/purchases accepts purchase payloads. Recommendation runs exist (2 runs in DB — get their IDs).

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/bootstrap.py` — add seed purchase data or a `seed_purchases()` function

## Implementation Steps

1. **Inspect existing purchase schema**
   ```bash
   cd backend && .venv/bin/python -c "
   import sys; sys.path.insert(0,'src')
   from szimplacoffee.db import engine
   from sqlalchemy import text
   c = engine.connect()
   print(c.execute(text('PRAGMA table_info(purchase_history)')).fetchall())
   print('Sample:', c.execute(text('SELECT * FROM purchase_history LIMIT 2')).fetchall())
   print('Rec runs:', c.execute(text('SELECT id FROM recommendation_runs')).fetchall())
   print('Products:', c.execute(text('SELECT id, name FROM products LIMIT 5')).fetchall())
   print('Merchants:', c.execute(text('SELECT id, name FROM merchants WHERE trust_tier=\"trusted\" LIMIT 5')).fetchall())
   "
   ```

2. **Draft 5 realistic seed purchases**
   Use real merchant IDs, product IDs, and recommendation_run_ids from DB. Mix:
   - 3 purchases with recommendation_run_id set (from existing rec run IDs)
   - 2 purchases without recommendation link (organic buys)
   Include fields: merchant_id, product_id, variant_id (if available), purchase_price_cents, bag_weight_grams, purchased_at, notes

3. **Add seed_purchases() to bootstrap.py**
   - Check if purchase_history count already ≥ 10 before inserting (idempotent)
   - Insert 5 rows using SQLAlchemy session

4. **Run the seed**
   ```bash
   cd backend && .venv/bin/python -c "
   import sys; sys.path.insert(0,'src')
   from szimplacoffee.bootstrap import seed_purchases
   seed_purchases()
   "
   ```
   Or add a CLI command `szimpla seed-purchases` if bootstrap.py has a pattern for it.

5. **Verify**
   ```bash
   cd backend && .venv/bin/python -c "
   import sys; sys.path.insert(0,'src')
   from szimplacoffee.db import engine
   from sqlalchemy import text
   c = engine.connect()
   n = c.execute(text('SELECT COUNT(*) FROM purchase_history')).scalar()
   linked = c.execute(text('SELECT COUNT(*) FROM purchase_history WHERE recommendation_run_id IS NOT NULL')).scalar()
   print(f'Total: {n}, Linked: {linked}')
   assert n >= 10
   assert linked >= 3
   "
   ```

## Risks / Notes
- product_variants table may have its own IDs — query variant_id carefully
- If recommendation_run_id column not present in purchase_history (pre-SC-70 schema), check migration status
- Do not break existing 5 purchases — inserts only

## Verification
```bash
cd backend && .venv/bin/python -c "..." # count query above
```
Target: ≥10 total, ≥3 linked to recommendation runs

## Out of Scope
- UI changes
- New recommendation runs
- Brew feedback (already at 3, goal is met)
