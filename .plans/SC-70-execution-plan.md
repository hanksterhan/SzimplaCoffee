# SC-70 Execution Plan

## Goal
Add an optional recommendation_run_id foreign key to PurchaseHistory. Wire it through the API and PurchaseForm so purchases can be linked to the recommendation that suggested them.

## Context
Without a recommendation-to-purchase link, we cannot measure recommendation conversion. This is the feedback loop foundation. The field must be fully optional to preserve backward compatibility.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/models.py`
- `backend/src/szimplacoffee/api/history.py`
- `frontend/src/components/purchases/PurchaseForm.tsx`

## Implementation Steps
1. Add column to PurchaseHistory model in models.py:
   ```python
   recommendation_run_id: Mapped[Optional[int]] = mapped_column(
       ForeignKey("recommendation_runs.id", ondelete="SET NULL"), nullable=True
   )
   ```
2. Create Alembic migration:
   ```bash
   cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "add recommendation_run_id to purchase_history"
   alembic upgrade head
   ```
3. Verify column exists:
   ```bash
   cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; cols=[r[1] for r in engine.connect().execute(text('PRAGMA table_info(purchase_history)')).fetchall()]; print('recommendation_run_id' in cols)"
   ```
4. Update purchase create schema in history.py to accept recommendation_run_id (optional, nullable)
5. Update purchase response schema to include recommendation_run_id
6. Update PurchaseForm.tsx to accept optional recommendationRunId prop and include in POST body
7. Run frontend build and verify

## Risks / Notes
- Keep recommendation_run_id nullable at every layer — existing callers must not break
- If PurchaseForm doesn't have a prop system, add as hidden input populated from route state
- Alembic migration must run cleanly on existing DB

## Verification
```bash
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; cols=[r[1] for r in engine.connect().execute(text('PRAGMA table_info(purchase_history)')).fetchall()]; print('recommendation_run_id' in cols)"
curl -s -X POST http://localhost:8000/api/v1/history/purchases -H 'Content-Type: application/json' -d '{"product_id": 1, "merchant_id": 1, "price_paid": 18.0, "recommendation_run_id": null}' | python -m json.tool
cd frontend && npm run build 2>&1 | tail -3
```

## Out of Scope
- Analytics on recommendation conversion rate
- Auto-population of recommendation_run_id from URL params
