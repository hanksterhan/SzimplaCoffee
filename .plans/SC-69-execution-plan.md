# SC-69 Execution Plan

## Goal
Exercise the PurchaseForm UI with 5 real purchases and verify all records persist to the purchase_history table and are retrievable via API.

## Context
The purchase logging form has never been used with real data. This is a required step before the recommendation feedback loop can function. It also validates the form's backend integration.

## Files / Areas Expected to Change
- `frontend/src/components/purchases/PurchaseForm.tsx` (fix if broken)
- `backend/src/szimplacoffee/api/history.py` (fix if broken)

## Implementation Steps
1. Start the dev server: `./scripts/dev.sh`
2. Navigate to the purchases section in the UI
3. Log Purchase 1: pick a real product from the merchants list, set price, date, notes
4. Repeat for 4 more purchases with different products/merchants
5. After each: verify DB row created:
   ```bash
   cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT id, product_id, price_paid FROM purchase_history ORDER BY id DESC LIMIT 5')).fetchall())"
   ```
6. Verify API returns all 5:
   ```bash
   curl -s http://localhost:8000/api/v1/history/purchases | python -c "import json,sys; d=json.load(sys.stdin); print(len(d if isinstance(d,list) else d.get('items',d.get('purchases',[]))))"
   ```
7. Fix any form errors encountered; keep fix minimal

## Risks / Notes
- Form may fail if product_id field requires a product that exists in DB — use real product IDs from /api/v1/products
- Fix bugs found during exercise before marking AC complete
- Document any UX issues as follow-up tickets, do not block SC-69 on them

## Verification
```bash
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM purchase_history')).scalar())"
curl -s http://localhost:8000/api/v1/history/purchases | python -c "import json,sys; d=json.load(sys.stdin); print(len(d if isinstance(d,list) else d.get('items',[])))"
```

## Out of Scope
- Purchase-to-recommendation linkage (SC-70)
- Brew feedback (SC-71)
- UI redesign
