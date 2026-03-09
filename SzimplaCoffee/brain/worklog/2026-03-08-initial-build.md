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
- Added a merchant discovery queue with search-result harvesting and promotion flow
- Added richer promo extraction from homepage, shipping, FAQ, refund, and subscription pages
- Tightened product filtering to exclude equipment, instant formats, and pod-style formats
- Improved ranking with purchase-history fit, shot-style weighting, decaf control, and per-merchant diversity
- Promoted and crawled discovered merchants: Onyx Coffee Lab and Goshen Coffee

## Open issues

- WooCommerce size-level pricing is still heuristic in some cases
- Notion import is seeded rather than fully integrated
- Browser fallback is not wired up yet
- Discovery still needs better precision for custom-site merchants and content-heavy source pages
- Promo snapshots are intentionally source-rich but not yet deduped into canonical merchant promos

## Current live state

- 4 merchants
- 2 pending discovery candidates
- 111 products
- 333 variants
- 533 offer snapshots
- 104 promo snapshots
- 3 seeded purchase-history records
