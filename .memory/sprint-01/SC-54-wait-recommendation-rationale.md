# SC-54 Delivery Memory: Wait Recommendation Rationale

## What Changed

- Added `WAIT_SCORE_THRESHOLD = 0.30` constant to `recommendations.py`
- Added `build_wait_assessment(candidates, no_candidates)` function — returns `(wait: bool, rationale: str | None)`
- Updated `create_recommendation` and `today_buying_brief` endpoints to use `build_wait_assessment`
- `wait_recommendation` now triggers when best score < 0.30, not just when no candidates exist
- Added `wait_rationale: Optional[str]` to `RecommendationResultResponse`
- Updated Today page to show rationale string when wait is recommended
- Updated `TodayBriefResult` type with `wait_rationale` field

## Why It Matters

North-star says "the product must be allowed to say wait." The old implementation only said wait when there were literally zero candidates. Now it also says wait when the best option scores below 0.30 — with a human-readable explanation.

## Threshold Design

0.30 is a conservative floor. The recommendation score range is roughly 0.0–0.8+ for real merchants. A score below 0.30 typically means: no history signal, weak quality profile, no espresso relevance, and overpriced. That's a clear "wait."

## Follow-ups

- Consider adding predicted-sale timing rationale (requires price history patterns)
- Consider exposing WAIT_SCORE_THRESHOLD as a user-configurable preference
