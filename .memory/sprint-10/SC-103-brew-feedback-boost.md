# SC-103 — Brew feedback boost in recommendation scoring

## What changed

- Added positive brew-feedback weighting to `build_recommendations()` so highly rated coffees now receive a recommendation score boost instead of feedback being purely punitive.
- Introduced:
  - `BREW_BOOST_THRESHOLD = 8.0`
  - `BREW_BOOST_WEIGHT = 0.08`
  - `BREW_BOOST_MULTI_SESSION_WEIGHT = 0.12`
- Materialized both average rating and feedback count per product from `brew_feedback`.
- Preserved the existing low-rating penalty path (`BREW_PENALTY_WEIGHT`) for poorly performing coffees.
- Threaded `brew_session_count` into `RecommendationCandidate` and API output.
- Extended `score_breakdown` with `brew_session_count` and `brew_boost` so explainable recommendations show the positive signal explicitly.
- Added a buyer-facing pro string: `Proven performer (N brew session[s])` when a boost is applied.

## Why this shape

The existing learning loop only prevented bad repeats. It did not help autopilot or the UI favor coffees that already brewed especially well. A small additive boost is the minimal safe change: it surfaces strong personal signal without destabilizing the rest of the scoring model.

Multi-session products get a slightly stronger boost than one-off successes to reward consistency.

## Verification

- `cd backend && . .venv/bin/activate && pytest tests/test_recommendations.py -q` → 31 passed
- `cd backend && . .venv/bin/activate && pytest tests/ -q` → 294 passed
- `cd backend && ~/.local/bin/ruff check src/ tests/` → passed

## Sharp edges / follow-ups

- Boost weights are intentionally conservative; real-world recommendation ordering should be observed before increasing them.
- The API now exposes `brew_session_count`, but no dedicated UI treatment beyond `pros` exists yet.
- This still works at the product level, not the shot-style level. A future refinement could weight feedback only when `shot_style` matches the current recommendation request.
