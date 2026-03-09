# 2026-03-08 Initial Build

## Completed

- Created the Python app skeleton
- Added SQLite-backed models
- Added platform detection
- Added adapter-first crawling for Shopify and WooCommerce
- Added recommendation scoring
- Added a local web UI
- Added bootstrap data and a second-brain baseline
- Verified bootstrap with live merchant data from Olympia Coffee Roasting Company and Camber Coffee
- Verified the app routes render and recommendations return current catalog results

## Open issues

- WooCommerce size-level pricing is still heuristic in some cases
- Notion import is seeded rather than fully integrated
- Browser fallback is not wired up yet
- Merchant discovery beyond manual add is not implemented yet

## Current live state

- 2 trusted merchants
- 43 products
- 105 variants
- 105 offer snapshots
- 2 promo snapshots
- 3 seeded purchase-history records
