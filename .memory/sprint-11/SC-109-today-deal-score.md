# SC-109 — Today view deal-score: baseline deal_score, deal_badge, blended ranking

**Delivered:** 2026-03-20  
**Branch:** SC-109-today-deal-score  
**Tests:** 327 passed (19 new in test_deal_score.py)

## What Changed

### Backend — `services/recommendations.py`
- Added `_baseline_deal_score(session, variant_id, current_price_cents)` helper that
  queries `VariantPriceBaseline.median_price_cents` and computes:
  - `deal_score = (median - current) / median`, clamped [-1, 1]
  - `deal_badge`: great_deal (≥15% below) / good_deal (5–15%) / at_baseline (±5%) /
    above_baseline (>5% above) / no_baseline (no record)
- Updated `RecommendationCandidate` dataclass: added `deal_score`, `deal_badge` fields.
- Changed ranking formula from direct sum to blended total:
  `total = QUALITY_BLEND_WEIGHT (0.7) * base_composite + DEAL_BLEND_WEIGHT (0.3) * max(0, deal_score)`
  - Quality still dominates; deal acts as tiebreaker when baselines exist.
  - `above_baseline` (negative deal_score) is clamped to 0 contribution — doesn't penalize.
  - No baseline → neutral (0 contribution), not a penalty.
- Enhanced `build_wait_assessment`: emits deal-aware "wait" signal when best candidate
  is `above_baseline` and quality score is borderline (< WAIT_THRESHOLD + 0.10).
- Added `deal_score`, `deal_badge` fields to score_breakdown dict.

### Backend — `api/recommendations.py`
- Added `deal_score: Optional[float]` and `deal_badge: Optional[str]` to
  `RecommendationCandidateOut` Pydantic schema.

### Frontend — `hooks/use-today.ts`
- Added `deal_score: number | null` and `deal_badge: string | null` to
  `TodayRecommendationCandidate` interface.

### Frontend — `routes/today.lazy.tsx`
- Added `BaselineDealBadge` component that renders:
  - `🔥 Great deal` (emerald, great_deal)
  - `✓ Good deal` (green, good_deal)
  - `↑ Above baseline` (orange, above_baseline)
  - Nothing for at_baseline or no_baseline
- Renders `BaselineDealBadge` alongside existing `DealBadge` in TopPickCard and RunnerUpCard.

### Tests — `tests/test_deal_score.py` (new, 19 tests)
- `TestBaselineDealScore`: no_baseline, zero_median, great/good/at/above/clamped scenarios
- `TestDealBadgeBoundaries`: boundary values at 15%, 14%, 5%, 3% below, 5% above
- `TestBlendConstants`: weights sum to 1.0, quality dominates
- `TestBlendedRanking`: deal tiebreaker, None neutrality, above_baseline non-boost

### Tests — `tests/test_recommendations.py` (updated)
- Fixed 3 brew_feedback assertions: `baseline ± weight` → `baseline ± QUALITY_BLEND_WEIGHT * weight`
  because brew weights are inside `base_composite`, which is multiplied by 0.7 in the blend.

## Surprises / Lessons

- The badge boundary check was initially off-by-one: using negative constant `_DEAL_BADGE_ABOVE (-0.05)`
  as `> deal_score > _DEAL_BADGE_ABOVE` caused at_baseline to fail at 0.0 (equal to baseline).
  Fixed to explicit numeric literals with clear comment blocks.
- Blending via QUALITY_BLEND_WEIGHT broke 3 existing brew test assertions that assumed additive
  score arithmetic. The fix is simple (multiply expected delta by 0.7) but tests needed updating.
- The Today view already had deal intelligence via VariantDealFact (SC-100) — the new
  BaselineDealBadge is additive, not a replacement. Both can show on the same card.
- The `/api/v1/recommendations/today` route returns candidates via `asdict()` — no change needed
  as new dataclass fields flow through automatically.

## Follow-ups

- SC-108 (catalog quality sort) is still open — p2, unblocked.
- The `deal_badge` field is not yet exposed in the `/recommendations` POST response schema
  for the full recommend.lazy.tsx page — that's a future enhancement (not in SC-109 scope).
- When more baseline data accumulates (>90 days of crawl history), deal scoring will become
  more meaningful. Merchant crawl cadence drives baseline sample count.
