# Now / Next / Later

_Updated: 2026-03-18 after SC-78 delivery_

## Top-500 Merchant Registry — Rollout Policy (SC-53)

### Trust Tiers
- **Tier A (trusted/verified)**: Merchants with verified order history, strong metadata, clear roast-date practices, and consistent espresso relevance. Crawled every 6h. Appear in all buying views.
- **Tier B (candidate)**: Promising merchants with good platform detection and reasonable quality scores. Crawled every 24h. Appear in catalog browser, eligible for buying views once quality floor is met.
- **Tier C (candidate)**: Long-tail merchants. Crawled weekly. Used for discovery and browsing, not default buying recommendations.
- **Tier D (rejected/excluded)**: Not auto-crawled. Retained in registry for audit trail. Never shown in recommendations.

### Inclusion Thresholds for Buying Views
- `trust_tier` must be in {trusted, verified, candidate}
- `crawl_tier` must not be D
- `overall_quality_score >= 0.4` (if a quality profile exists)
- Merchants without a quality profile are optimistically included

### Coverage Growth Path
1. Start with ~10-20 Tier A merchants (Olympia, Camber, known trusted roasters)
2. Add Tier B candidates from the seed list (`SzimplaCoffee/brain/merchants/top-500-seed.md`)
3. Crawl weekly, review quality and trust automatically
4. Promote candidates to trusted after 2+ verified purchases or strong crawl quality
5. Reject merchants with persistent crawl failures, poor metadata, or no espresso relevance

### Quality Floor Justification
- 0.4 is a low floor intentionally — new merchants have no data yet
- As crawl history accumulates, the floor can be raised
- The personal profile (has_order_history, would_reorder) provides additional signal

---

## Now

- Deliver SC-72 so brew feedback ratings affect recommendation ranking
- Keep the ready backlog replenished after SC-78; SC-80 is the next purchases UX follow-on
- Add the recommendation-page handoff into `/purchases?recommendationRunId=<id>` once the next purchase-loop slice is selected

## Next

- Surface recommendation linkage in purchase history/detail (SC-80)
- Add crawl health, crawl error, and stale-data visibility in the Watch/Review UI
- Import real purchase history from Notion instead of relying on seed data
- Add richer merchant filtering and sorting in the dashboard and discovery queue
- Raise buying quality floor to 0.5 once 3+ months of crawl data exist

## Later

- Add authenticated wallet-credit ingestion (Shop Cash, store credits)
- Add broader merchant discovery sources beyond search-result listicles
- Add cloud sync only if local-first usage proves limiting
- Add ML-based quality scoring once enough feedback data exists
