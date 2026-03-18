# SC-66 Execution Plan

## Goal
Fix the recommendation engine so it returns at least one ranked candidate when products with offer_snapshots exist. Change is minimal — do not alter scoring algorithm intent.

## Context
SC-65 diagnosed the elimination path. This ticket applies the fix based on that diagnosis. The fix must be surgical: relax only the filter that incorrectly eliminates valid candidates.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/recommendations.py`
- `backend/tests/` (regression test)

## Implementation Steps
1. Read the SC-65 diagnosis from delivery memory
2. Identify the specific filter/query causing empty results (e.g., trust_tier threshold, deal_fact join, offer_snapshot recency)
3. Apply minimum fix:
   - If trust_tier filter is too strict: lower threshold from A-only to B+
   - If offer_snapshot join is inner join on empty table: check/relax
   - If VariantDealFact join required: add fallback path using offer_snapshots directly
4. Verify recommendations return results:
   ```bash
   curl -s -X POST http://localhost:8000/api/v1/recommendations \
     -H 'Content-Type: application/json' \
     -d '{"current_inventory_grams": 0}' | python -m json.tool
   ```
5. Write regression test in tests/:
   - Seed 1 merchant (tier B), 1 product, 1 offer_snapshot
   - Assert recommendation returns >=1 result

## Risks / Notes
- Do NOT lower the wait threshold for inventory >= 900g — that behavior is intentional
- If the fix requires relaxing quality criteria, document the trade-off
- Keep the fix reversible in case it has unintended side effects

## Verification
```bash
curl -s -X POST http://localhost:8000/api/v1/recommendations -H 'Content-Type: application/json' -d '{"current_inventory_grams": 0}' | python -c "import json,sys; d=json.load(sys.stdin); r=d.get('results',d.get('recommendations',[])); print(len(r),'results')"
cd backend && pytest tests/ -v -k recommendation
cd backend && ruff check src/szimplacoffee/services/recommendations.py
```

## Out of Scope
- Explain mode (SC-67)
- Scoring algorithm improvements
- Frontend changes
