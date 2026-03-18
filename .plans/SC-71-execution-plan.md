# SC-71 Execution Plan

## Goal
Exercise the BrewFeedbackForm with 3 real brew sessions including rating and notes. Verify records persist and are API-accessible.

## Context
Brew feedback is the primary signal for penalizing poor-quality products in recommendations. Without real feedback data, SC-72 cannot be tested meaningfully.

## Files / Areas Expected to Change
- `frontend/src/components/purchases/BrewFeedbackForm.tsx` (fix if broken)
- `backend/src/szimplacoffee/api/history.py` (fix if broken)

## Implementation Steps
1. Navigate to the brew feedback section in the UI
2. Log Brew Session 1:
   - Link to a purchase from SC-69
   - Brew method: V60 (or preferred method)
   - Rating: 4/5
   - Notes: "Clean, bright acidity. Good clarity."
3. Log Brew Session 2:
   - Different product
   - Rating: 2/5
   - Notes: "Flat, dull. Likely stale."
4. Log Brew Session 3:
   - Rating: 5/5
   - Notes: "Excellent sweetness, long aftertaste."
5. Verify DB rows:
   ```bash
   cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT id, rating, notes FROM brew_feedback ORDER BY id DESC LIMIT 5')).fetchall())"
   ```
6. Verify API response:
   ```bash
   curl -s http://localhost:8000/api/v1/history/brew-feedback | python -c "import json,sys; d=json.load(sys.stdin); print(len(d if isinstance(d,list) else d.get('items',d.get('feedback',[]))))"
   ```
7. Fix any form errors found; keep fix minimal

## Risks / Notes
- Form may require a linked purchase_id — use purchases from SC-69
- API endpoint URL may differ from assumed — check history.py for actual route
- Document UX issues as follow-up, do not block SC-71 on them

## Verification
```bash
cd backend && python -c "from szimplacoffee.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT COUNT(*) FROM brew_feedback')).scalar())"
curl -s http://localhost:8000/api/v1/history/brew-feedback | python -m json.tool | head -30
```

## Out of Scope
- Wiring feedback into recommendation ranking (SC-72)
- UI redesign
