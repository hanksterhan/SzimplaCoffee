# SC-56 Execution Plan

## Goal

Add personal inventory awareness so the recommendation engine can factor in how much coffee the user currently has.

## Context

North-star: "Bag size must change the recommendation. Bulk discounts matter, but they only matter if the user can realistically use the coffee well. The product should optimize for usable value, not theoretical unit economics."

Currently, the system has no way to know the user's current inventory. A user with 3lb on hand should not get a "buy 5lb" recommendation.

## Files Expected to Change

- `backend/src/szimplacoffee/models.py` — add `inventory_on_hand_grams` to `MerchantPersonalProfile` or a separate `UserInventory` entry
- `backend/src/szimplacoffee/services/recommendations.py` — use inventory in quantity scoring
- `backend/src/szimplacoffee/api/recommendations.py` — accept `current_inventory_grams` in request
- `frontend/src/routes/today.lazy.tsx` — add inventory input
- `frontend/src/hooks/use-today.ts` — pass inventory to API

## Implementation Steps

1. Add `inventory_on_hand_grams: int | None` to a new `UserPreferences` singleton model (or use the existing PersonalProfile singleton row)
2. Add `current_inventory_grams: int = 0` to `RecommendationRequest`
3. In `_quantity_score()`: if `current_inventory_grams > 450g (1lb)`, down-score large bags
4. In wait threshold logic: if inventory_on_hand > 900g (2lb), set `wait_rationale = "you still have coffee at home"`
5. Update `RecommendationRequestPayload` schema to accept `current_inventory_grams`
6. Add inventory slider/input to Today page

## Risks / Notes

- Use 450g (~1lb) and 900g (~2lb) as thresholds — matches common bag sizes
- Keep as optional input; system works fine without it

## Verification

- `pytest -q` — tests for inventory-adjusted quantity scoring
- `npm run build` — today page builds with inventory input

## Out of Scope

- Per-bag freshness tracking
- Automated deduction from purchases
- Multi-user or household inventory
