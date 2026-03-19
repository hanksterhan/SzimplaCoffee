# SC-88 Execution Plan

## Goal
Add a metadata fill-rate card to the dashboard that shows origin/process/roast/variety fill percentages. Backend API extended; frontend component added.

## Context
Dashboard currently shows summary metrics. No metadata quality visibility. Four fill-rate fields need to be computed and surfaced. Backend change first, then frontend.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/api/dashboard.py`
- `backend/src/szimplacoffee/schemas/dashboard.py`
- `backend/tests/test_dashboard.py`
- `frontend/src/components/MetadataFillCard.tsx` (new)
- `frontend/src/routes/index.lazy.tsx`
- `frontend/src/api/schema.d.ts` (regenerated)

## Implementation Steps

### Slice S1 — Backend

1. **Add metadata_fill_rates to DashboardResponse schema**
   ```python
   class MetadataFillRates(BaseModel):
       origin_pct: int
       process_pct: int
       roast_pct: int
       variety_pct: int

   class DashboardResponse(BaseModel):
       ...existing fields...
       metadata_fill_rates: MetadataFillRates
   ```

2. **Compute in dashboard API endpoint**
   ```python
   total = db.execute(select(func.count()).select_from(Product)).scalar() or 1
   origin_pct = round(100 * db.execute(
       select(func.count()).where(Product.origin_country.isnot(None), Product.origin_country != '')
   ).scalar() / total)
   # repeat for process_family, roast_level, variety_text
   ```

3. **Add pytest coverage**
   - Test that API returns `metadata_fill_rates` dict with 4 integer fields

4. **Run tests**
   ```bash
   cd backend && .venv/bin/pytest tests/ -q
   ```

### Slice S2 — Frontend

5. **Regenerate API types**
   ```bash
   cd frontend && npm run gen:api
   ```
   (Backend must be running on port 8000)

6. **Create MetadataFillCard component**
   - Props: `fills: { origin_pct, process_pct, roast_pct, variety_pct }`
   - Render a card with 4 labeled progress bars or stat rows
   - Color: green ≥70%, yellow 50–69%, red <50%

7. **Add card to Dashboard page**
   - Import MetadataFillCard into `routes/index.lazy.tsx`
   - Pass `data.metadata_fill_rates` from useDashboard() hook

8. **Build check**
   ```bash
   cd frontend && npm run build
   ```

## Risks / Notes
- If backend is not running during npm run gen:api, schema.d.ts won't update — document this
- Keep MetadataFillCard visually consistent with existing dashboard cards (shadcn/ui Card component)

## Verification
```bash
cd backend && .venv/bin/pytest tests/ -q
cd frontend && npm run gen:api && npm run build
```

## Out of Scope
- Per-merchant metadata breakdown
- Historical fill rate charts
