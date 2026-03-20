# Now / Next / Later

_Updated: 2026-03-20 after SC-102 delivery_

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

- Improve origin fill rate on active coffee products; process and roast are now materially healthier after SC-102
- Keep Phase 2 focused on trustworthy data semantics before broader feature expansion

## Next

- Create the next origin-coverage ticket using richer crawl text / stored descriptions rather than more parser-only guesses
- Revisit frontend filter semantics so `unknown` and non-coffee rows never pollute catalog filter UX
- Deliver SC-104 to persist description text and unlock origin/process extraction beyond title-only parsing
- Deliver SC-105 to import the next 10 merchants from the seed list using `--crawl-now` serially
- Observe recommendation ordering after SC-103 brew-feedback boost and adjust weights only if ranking drift is observed
- Raise buying quality floor to 0.5 once crawl/data confidence supports it

## Later

- Add authenticated wallet-credit ingestion (Shop Cash, store credits)
- Add broader merchant discovery sources beyond search-result listicles
- Add cloud sync only if local-first usage proves limiting
- Add ML-based quality scoring once enough feedback data exists
