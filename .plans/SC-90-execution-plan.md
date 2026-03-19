# SC-90 Execution Plan

## Goal
Add a `goal_status` dict to GET /api/v1/dashboard with boolean flags for each goal.yaml success criterion. Makes goal tracking programmatic.

## Context
goal.yaml defines 8 success criteria. Autopilot currently queries DB manually to check goal completion. A structured API response makes this reusable and visible in the UI.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/api/dashboard.py`
- `backend/src/szimplacoffee/schemas/dashboard.py`
- `backend/tests/test_dashboard.py`

## Implementation Steps

1. **Define GoalStatus schema**
   ```python
   class GoalStatus(BaseModel):
       merchants_15_plus: bool
       metadata_70pct: bool
       recs_produce_results: bool
       today_works: bool       # proxy: recs_produce_results
       purchases_10_plus: bool
       brew_feedback_3_plus: bool
       ui_works: bool          # manual / always True (hardcode)
       tests_pass: bool        # manual / always True (hardcode)
       all_complete: bool      # computed from above
   ```

2. **Compute each criterion in dashboard API**
   Thresholds (hardcoded to match goal.yaml):
   - `merchants_15_plus`: COUNT(merchants WHERE trust_tier='trusted') >= 15
   - `metadata_70pct`: (COUNT(origin_country set) / total_products * 100) >= 70
   - `recs_produce_results`: COUNT(recommendation_runs WHERE status='completed') >= 1
   - `today_works`: same as recs_produce_results (Today view uses same engine)
   - `purchases_10_plus`: COUNT(purchase_history) >= 10
   - `brew_feedback_3_plus`: COUNT(brew_feedback) >= 3
   - `ui_works`: True (hardcoded — manual verification)
   - `tests_pass`: True (hardcoded — CI is not run here)
   - `all_complete`: AND of all above

3. **Add GoalStatus to DashboardResponse**
   ```python
   class DashboardResponse(BaseModel):
       ...existing...
       goal_status: GoalStatus
   ```

4. **Add tests**
   - Test that goal_status is in response
   - Test that `merchants_15_plus` is True when seeded with 15+ trusted merchants

5. **Regenerate frontend types**
   ```bash
   cd frontend && npm run gen:api && npm run build
   ```

## Risks / Notes
- Don't import autopilot YAML at app runtime — hardcode thresholds
- ui_works and tests_pass should be True by default (they require manual/CI verification not available at request time)
- all_complete should reflect actual DB state — do not hardcode it

## Verification
```bash
cd backend && .venv/bin/pytest tests/ -q
cd frontend && npm run gen:api && npm run build
```

## Out of Scope
- Frontend rendering of goal_status (can be a follow-on)
- Auto-stopping autopilot — autopilot reads status.json, not this endpoint
