# SC-109 Execution Plan

## Goal

Integrate SC-107's VariantPriceBaseline into the recommendation engine to produce deal-scored, blended-ranked recommendations with deal badges surfaced in the Today view.

## Context

SC-107 adds VariantPriceBaseline. This ticket wires that data into the recommendation scoring pipeline and the Today view UI. The result is the Phase 3 core capability: recommendations that combine quality and deal intelligence.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/services/recommendation_service.py` — add deal_score, blended ranking
- `backend/src/szimplacoffee/schemas/recommendations.py` — add deal_score and deal_badge fields
- `backend/tests/test_deal_score.py` — new test file
- `frontend/src/routes/today.lazy.tsx` — render deal badge chips
- `frontend/src/api/schema.d.ts` — regenerated after backend schema change (via npm run gen:api)

## Implementation Steps

1. **Read recommendation_service.py** to understand current scoring pipeline and RecommendationItem structure.
2. **Read schemas/recommendations.py** to understand current response shape.
3. **Add deal_score computation**: when scoring a variant, join VariantPriceBaseline. Compute `deal_score = (baseline_price - current_price) / baseline_price`. Clamp to [-1, 1]. If no baseline, deal_score = None.
4. **Assign deal_badge**: great_deal < -0.15, good_deal < -0.05, at_baseline ±0.05, above_baseline > 0.05, no_baseline when deal_score is None.
5. **Blended ranking**: `final_score = 0.7 * quality_score + 0.3 * max(0.0, deal_score or 0.0)`. Add quality_weight and deal_weight as configurable constants (module-level, easy to tune).
6. **Update RecommendationItem schema**: add `deal_score: Optional[float]`, `deal_badge: Optional[str]`.
7. **Write test_deal_score.py**: test deal_score computation, badge assignment, blended ranking with mock baseline data.
8. **Regenerate frontend API types**: `cd frontend && npm run gen:api` (backend must be running).
9. **Update today.lazy.tsx**: render a `<Badge>` or small chip for deal_badge. Labels: great_deal="🔥 Great deal", good_deal="✓ Good deal", at_baseline="— Baseline", above_baseline="↑ Above". Only show when deal_badge is not null or 'no_baseline'.
10. **Run verification**: `pytest tests/ -q`, `npm run build && npx tsc -b`.

## Risks / Notes

- Blocked on SC-107: VariantPriceBaseline must exist before this ticket can be implemented.
- If no baselines exist (fresh DB), all deal_scores will be null — Today view should still work, just without badges.
- Deal weight of 0.3 is a starting point — can be tuned after observing real deal frequency.
- The "wait" recommendation path already exists in recommendation_service.py — enhance it to also check if deal_score < threshold when quality is borderline.
- gen:api requires the backend server to be running — plan for this in the delivery run.

## Verification

1. `cd backend && pytest tests/ -q`
2. `cd frontend && npm run build && npx tsc -b`
3. `cd backend && ~/.local/bin/ruff check src/ tests/`
4. Manual: run a recommendation from the Today view, confirm deal badges appear.

## Out of Scope

- Subscription deal integration
- Price trend history charts
- Catalog sort changes (SC-108)
- Email or push notifications for deals
