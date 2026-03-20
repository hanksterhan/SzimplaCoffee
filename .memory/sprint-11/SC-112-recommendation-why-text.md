# SC-112 — Recommendation explainability: why_text narrative

**Delivered:** 2026-03-20  
**Branch:** sc-112-recommendation-why-text → merged to stage

## What changed

- Added `why_text: str` field to `RecommendationCandidate` dataclass (default `""`)
- New `_build_why_text()` function in `services/recommendations.py` — template-based, no LLM
- Fragments drawn from: `deal_badge` + price drop %, `compare_at_discount_percent`, `merchant_score`,
  `brew_avg_rating + brew_session_count`, `origin_country/origin_text`, `process_family/process_text`
- Compose logic: first sentence = primary signal, second sentence = up to 2 secondary fragments
- `why_text` exposed on `RecommendationCandidateOut` API schema (no migration needed — computed at runtime)
- Frontend: `why_text` added to `TodayRecommendationCandidate` TypeScript type
- Frontend: `TopPickCard` in `today.lazy.tsx` renders `why_text` as a small italic amber paragraph
  above the pros list when non-empty

## Tests

- 9 unit tests in `backend/tests/test_recommendation_why_text.py` covering all branches
- 354 total backend tests pass
- Ruff clean, frontend build + tsc clean

## Surprises / notes

- `_build_why_text` receives `Product` object but accesses `.origin_country`, `.origin_text`,
  `.process_family`, `.process_text` — all already on the model, so no new queries needed
- The `today_buying_brief` route uses `asdict(top)` so `why_text` propagates automatically
- `why_text` is NOT persisted in `RecommendationRun` (lean storage intent preserved)
- The `f"priced within range of its historical low"` string initially had an unnecessary f-prefix;
  caught and fixed by ruff

## Follow-ups

- Alternatives cards in Today view don't show `why_text` — could be a future enhancement
- The `/recommendations` POST response also includes `why_text` but the recommendations list
  view doesn't render it yet
