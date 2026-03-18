# SC-72 Execution Plan

## Goal
Wire brew feedback scores into recommendation ranking by applying a configurable penalty to products with avg brew rating < 3.0.

## Context
Brew feedback data collected in SC-71 gives us rating signals. The recommendation engine should down-rank products that have been brewed and rated poorly. Products with no feedback should not be penalized.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/recommendations.py`
- `backend/tests/test_recommendations.py`

## Implementation Steps
1. Add a constant at the top of recommendations.py:
   ```python
   BREW_PENALTY_WEIGHT = 0.15  # Score deduction for avg rating < 3.0
   BREW_PENALTY_THRESHOLD = 3.0
   ```
2. Add a query to fetch avg brew rating per product_id:
   ```python
   brew_ratings = db.execute(
       text("SELECT product_id, AVG(rating) as avg_rating FROM brew_feedback GROUP BY product_id")
   ).fetchall()
   brew_rating_map = {r.product_id: r.avg_rating for r in brew_ratings}
   ```
3. In the scoring loop, apply penalty:
   ```python
   avg_rating = brew_rating_map.get(product.id)
   if avg_rating is not None and avg_rating < BREW_PENALTY_THRESHOLD:
       score -= BREW_PENALTY_WEIGHT
   ```
4. Write pytest tests in test_recommendations.py:
   - Test case 1: product with no feedback — score unchanged
   - Test case 2: product with avg rating 4.0 — no penalty
   - Test case 3: product with avg rating 2.0 — BREW_PENALTY_WEIGHT subtracted
5. Run ruff and pytest

## Risks / Notes
- Do not penalize products with no brew data — absence of data is neutral
- BREW_PENALTY_WEIGHT should be proportional to the score range — 0.15 is a reasonable default
- If recommendations use a normalized 0-1 score, 0.15 is ~15% penalty

## Verification
```bash
cd backend && pytest tests/test_recommendations.py -v -k brew
cd backend && ruff check src/szimplacoffee/services/recommendations.py tests/test_recommendations.py
grep -n "BREW_PENALTY" backend/src/szimplacoffee/services/recommendations.py
```

## Out of Scope
- UI for viewing brew feedback impact on score
- Merchant-level aggregation
- Automatic exclusion (not just penalty) for zero-rated products
