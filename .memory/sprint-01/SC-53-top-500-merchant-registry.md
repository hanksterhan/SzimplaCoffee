# SC-53 Delivery Memory: Top-500 Merchant Registry

## What Changed

### Backend
- Added registry tier constants to `services/discovery.py`:
  - `TRUST_TIER_TRUSTED/VERIFIED/CANDIDATE/REJECTED`
  - `CRAWL_TIER_A/B/C/D`
  - `BUYING_VIEW_TRUSTED_TIERS`, `CATALOG_VIEW_TIERS`, `BUYING_QUALITY_FLOOR`
  - `meets_buying_threshold(merchant)` — authoritative gate function
- Updated `build_recommendations()` to filter out sub-threshold merchants
- Updated `build_biggest_sales()` to filter out sub-threshold merchants
- Added `GET /api/v1/merchants/registry-summary` endpoint
- 12 new tests in `test_registry_thresholds.py`

### Documentation
- Updated `README.md` with Merchant Registry and Top-500 Rollout Policy section
- Updated `SzimplaCoffee/brain/backlog/now-next-later.md` with rollout policy and trust/crawl tier documentation

## Quality Threshold Design

- `BUYING_QUALITY_FLOOR = 0.4` is intentionally low — new merchants have no data
- Merchants with no quality profile are **optimistically included** (better UX for first crawl)
- As data accumulates, the floor should be raised to ~0.5

## Why `candidate` Tier Is In Buying Views

The north-star says: "coverage is important for discovery, trust is important for ranking." Excluding all candidates would mean new high-quality merchants never appear until manually promoted. The quality floor + crawl tier D exclusion handles the actual low-trust filtering.

## Follow-ups

- Raise quality floor to 0.5 after 3+ months of crawl data
- Add "trust promotion" workflow — auto-promote after N verified orders
- Seed `SzimplaCoffee/brain/merchants/top-500-seed.md` with real merchant list
