# 2026-03-19 — SC-103 brew feedback boost

Delivered SC-103.

## Summary

- Added positive brew-feedback weighting to recommendation scoring.
- High-rated coffees now receive a small boost; multi-session successes get a slightly larger one.
- Existing low-rating penalty remains intact.
- Recommendation API now exposes `brew_session_count`, and explain_scores now includes `brew_boost`.
- Added regression coverage for boost, stronger multi-session boost, API exposure, and Proven performer pros.

## Verification

- `pytest tests/test_recommendations.py -q` → 31 passed
- `pytest tests/ -q` → 294 passed
- `ruff check src/ tests/` → passed

## Notes

This is the first recommendation-scoring change that uses the personal learning loop as a positive ranking signal rather than only a guardrail.
