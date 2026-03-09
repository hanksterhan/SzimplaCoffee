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
- Upgraded discovery precision for custom merchants by recognizing Squarespace coffee-commerce sites
- Replaced raw promo pileups with canonical merchant-level promos while preserving promo snapshots
- Replaced WooCommerce size-price interpolation with exact whole-bean variation prices when public product pages expose them
- Tightened WooCommerce parsing after a live Camber validation failure so Bernardina and bundle products use exact prices, exact weights, and page-context fields
- Added product image URLs to the catalog and surfaced them in recommendation and merchant-detail views
- Added weight formatting and price-per-ounce display in the UI, including pounds when appropriate
- Added outbound site and product links that open in a new tab
- Switched add-merchant and refresh-crawl flows to queued background crawls with live status polling on the merchant page
- Removed manual crawl-tier input and now assign crawl tier automatically from platform type and crawlability

## Open issues

- Notion import is seeded rather than fully integrated
- Browser fallback is not wired up yet
- Some custom merchants are discoverable but still only use the generic crawler
- Promo extraction still needs stronger false-positive suppression for aggressive marketing copy
- Crawl health and per-merchant failure visibility need a first-class UI

## Current live state

- 5 merchants
- 2 pending discovery candidates
- 111 products
- 351 variants
- 1451 offer snapshots
- 142 promo snapshots
- 7 canonical merchant promos
- 3 seeded purchase-history records
