# SC-67 — Explain Scores: Backend API

**Delivered:** 2026-03-18T11:45 UTC  
**Commit:** c64f787  
**Tests:** 132 green (was 129, +3 new explain-mode tests)

## What Changed

- `RecommendationRequest` gains `explain_scores: bool = False`
- `RecommendationCandidate` gains `score_breakdown: dict | None`
- New `FilteredCandidate` dataclass with `filter_reason`
- `build_recommendations()` now returns `tuple[list[RecommendationCandidate], list[FilteredCandidate]]`
- All callers updated (API, CLI, tests) for tuple return
- `POST /api/v1/recommendations` with `explain_scores=True` returns:
  - `score_breakdown` per candidate (merchant_score, quantity_score, espresso_score, deal_score, freshness_score, history_score, promo_bonus, total + weights)
  - `filtered_candidates` list with filter_reason per excluded variant
- Default behavior unchanged when `explain_scores=False`

## Notes

- score_breakdown is stripped from persisted RecommendationRun JSON to keep storage lean
- The weights dict in breakdown makes it easy to spot ranking sensitivity at a glance
- SC-77 (frontend explain toggle) is the natural next piece
