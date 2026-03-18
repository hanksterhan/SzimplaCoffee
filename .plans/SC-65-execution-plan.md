# SC-65 Execution Plan

## Goal
Trigger the first real recommendation run via API and identify the exact step where candidates are eliminated. Document root cause in delivery memory.

## Context
The recommendation engine returns empty or wait. The cause is unknown — it could be empty offer_snapshots, VariantDealFact not populated, trust tier filters, or scoring thresholds. This ticket is diagnosis-first.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/recommendations.py` (add trace logging)
- `backend/tests/` (optional: capture response as fixture)

## Implementation Steps
1. Inspect current recommendations.py — trace the candidate pipeline from DB query to output
2. Identify all filter/scoring stages
3. Add trace logging (logger.debug) at each stage showing candidate count:
   ```python
   logger.debug("After trust filter: %d candidates", len(candidates))
   logger.debug("After offer_snapshot join: %d candidates", len(candidates))
   logger.debug("After deal_fact filter: %d candidates", len(candidates))
   ```
4. Start server and trigger recommendation:
   ```bash
   curl -s -X POST http://localhost:8000/api/v1/recommendations \
     -H 'Content-Type: application/json' \
     -d '{"current_inventory_grams": 0, "style": "pourover"}' | python -m json.tool
   ```
5. Try 3 different payloads: no inventory, 500g, espresso style
6. Capture debug logs from server output
7. Write diagnosis to delivery memory

## Risks / Notes
- Server must be running: `cd backend && uvicorn szimplacoffee.main:app --reload`
- Debug logging must be enabled: set LOG_LEVEL=DEBUG or check logging config
- Most likely cause: variant_deal_facts empty (SC-68) or offer_snapshots empty

## Verification
```bash
# API responds
curl -s -X POST http://localhost:8000/api/v1/recommendations -H 'Content-Type: application/json' -d '{"current_inventory_grams": 0}' | python -m json.tool

# Trace logs confirm candidate count at each stage
grep -n "candidate\|filter\|eliminated" backend/src/szimplacoffee/services/recommendations.py | head -20
```

## Out of Scope
- Fixing the root cause (SC-66)
- Explain mode (SC-67)
