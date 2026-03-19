# SC-89 Execution Plan

## Goal
Promote Coava Coffee to Tier A + trusted. Deactivate junk merchant rows (Blue Bottle D, Stumptownroasters D, Not A Url D) to clean the registry.

## Context
DB has 17 merchants. 13 are trusted Tier A. 4 are candidate/D/C:
- Coava Coffee Roasters: Tier C, candidate — has products, should be Tier A
- Blue Bottle Coffee: Tier D, candidate — duplicate/failed import
- Stumptownroasters: Tier D, candidate — duplicate of Stumptown Coffee
- Not A Url: Tier D, candidate — garbage record from bootstrap test

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/bootstrap.py` — add a `clean_merchant_registry()` function or inline migration script

## Implementation Steps

1. **Inspect current state**
   ```python
   SELECT id, name, crawl_tier, trust_tier, is_active, homepage_url
   FROM merchants
   ORDER BY crawl_tier, trust_tier
   ```

2. **Check Coava products**
   ```python
   SELECT COUNT(*) FROM products WHERE merchant_id = <coava_id>
   ```
   If products > 0, proceed with promotion.

3. **Update Coava**
   ```python
   UPDATE merchants SET crawl_tier='A', trust_tier='trusted' WHERE name LIKE '%Coava%'
   ```

4. **Deactivate junk merchants** (soft-delete via is_active=false)
   ```python
   UPDATE merchants SET is_active=false
   WHERE name IN ('Not A Url') OR (crawl_tier='D' AND trust_tier='candidate')
   ```
   Check carefully — only deactivate if no important data attached.

5. **Verify no orphaned active crawl_runs**
   ```python
   SELECT COUNT(*) FROM crawl_runs WHERE merchant_id IN (SELECT id FROM merchants WHERE is_active=false)
   ```
   Crawl runs are historical — fine to keep, just shouldn't trigger new crawls.

6. **Write migration helper in bootstrap.py**
   Add `clean_merchant_registry()` function that:
   - Promotes Coava if products > 5
   - Deactivates zero-product Tier D candidates
   - Is idempotent (check before update)

7. **Run tests**
   ```bash
   cd backend && .venv/bin/pytest tests/ -q
   ```

## Risks / Notes
- Do NOT hard-DELETE merchants — foreign keys from products, crawl_runs, offer_snapshots point to them
- Verify Blue Bottle product count before deactivating: `SELECT COUNT(*) FROM products WHERE merchant_id=(SELECT id FROM merchants WHERE name='Blue Bottle Coffee' AND crawl_tier='D')`
- Stumptownroasters may share some products with the real Stumptown entry — check before deactivating

## Verification
```bash
cd backend && .venv/bin/pytest tests/ -q
# Verify Coava is Tier A
cd backend && .venv/bin/python -c "..."
# Verify no active Tier D candidates
```

## Out of Scope
- Adding new merchants
- Frontend changes
