# SC-103 Execution Plan

## Goal

Use existing brew feedback data as a positive recommendation signal, not only a negative penalty, so products with proven excellent brew outcomes rank higher.

## Context

`build_recommendations()` already computes `brew_rating_by_product` and applies `BREW_PENALTY_WEIGHT` for products below `BREW_PENALTY_THRESHOLD`. There is no corresponding positive boost for strong products. Existing tests in `backend/tests/test_recommendations.py` already cover no-feedback and penalty behavior.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/services/recommendations.py`
- `backend/src/szimplacoffee/api/recommendations.py`
- `backend/tests/test_recommendations.py`

## Implementation Steps

1. Add `BREW_BOOST_THRESHOLD` and `BREW_BOOST_WEIGHT` constants in `recommendations.py`.
2. Materialize `brew_feedback_count_by_product` alongside `brew_rating_by_product`.
3. Compute `brew_boost` when avg rating is at or above threshold; scale slightly higher for 2+ sessions.
4. Include the boost in the total score calculation while preserving the existing penalty path.
5. Add a buyer-facing pro such as `Proven performer (N brew sessions)` when a boost is applied.
6. Extend `score_breakdown` to include `brew_session_count` and `brew_boost`.
7. Add regression tests for boosted, unboosted, and penalized cases.

## Risks / Notes

- Keep scoring changes small to avoid destabilizing recommendation ordering.
- Do not remove or weaken the existing penalty behavior.
- Keep API compatibility by making new breakdown fields optional/defaulted.

## Verification

- `cd backend && pytest tests/test_recommendations.py -q`
- `cd backend && pytest tests/ -q`
- `cd backend && ~/.local/bin/ruff check src/ tests/`

## Out of Scope

- New persistence fields for feedback aggregates
- UI-specific visual treatment beyond existing `pros` rendering
- Collaborative filtering or cross-user learning
