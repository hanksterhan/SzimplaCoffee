# SC-100: Today view deal badges from VariantDealFact

## What Changed
- `RecommendationCandidate` dataclass gained 4 new optional deal_fact fields: `deal_fact_baseline_30d_cents`, `deal_fact_price_drop_30d_percent`, `deal_fact_historical_low_cents`, `deal_fact_compare_at_discount_percent`.
- `build_recommendations()` now threads these values from the existing `fact` object (already in scope) into each candidate — zero extra DB queries.
- Frontend: `TodayRecommendationCandidate` interface extended to match.
- `DealBadge` component added to `today.lazy.tsx`: shows "🏆 Historical low" or "↓ N% below 30d avg" badge beside price when signals are present. 2% threshold prevents noise from trivial fluctuations.
- `RunnerUpCard` component replaced the old `SaleCard as unknown` hack for alternatives, providing proper typing and deal badge support.

## Why
Deal intelligence from VariantDealFact was already materialized but not threaded into the Today view recommendation cards, making the daily buying decision view less useful than the product catalog cards (which gained deal badges in SC-98).

## Approach
Chose to add flat fields to `RecommendationCandidate` dataclass rather than nesting a dict, to keep `asdict()` serialization clean and avoid type gymnastics in the frontend.

## Verification
- 275 backend tests pass
- `npm run build` clean
- `npx tsc -b` clean

## Follow-ups / Sharp Edges
- `deal_fact_price_drop_30d_percent` is threaded through but not used in DealBadge yet — the computed inline drop% from baseline_30d_cents is more reliable since it reflects effective (landed) price rather than raw offer price.
- SC-101 (merchant expansion) is next.
