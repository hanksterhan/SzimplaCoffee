# SC-43 — Products catalog UX polish

## What changed

- Added multi-select product category filtering to the `/products` page.
- Updated the products API to accept comma-separated categories.
- Added a conservative coffee fallback so the coffee filter can include likely whole-bean products that were mis-tagged as `merch`.
- Added derived summary metadata for product cards: primary price, primary weight, and whole-bean flag.
- Changed product cards to open an inline quick-view dialog instead of forcing immediate route navigation.
- Updated whole-bean cards to foreground merchant, price, and bag size.

## Why it changed

The catalog was still awkward for browsing and comparison. Single-select filters made category exploration clunky, and some legitimate coffees were disappearing from the default coffee view because of bad category tagging. Users also needed a faster way to inspect product metadata without leaving the catalog grid.

## Notes / sharp edges

- There is still no dedicated long-form product description field in the product schema. The quick view uses the best available metadata and falls back gracefully when detailed copy is unavailable.
- The coffee-like merch recovery is heuristic-based, not a full crawler/data-model fix.
- The standalone `/products/$productId` route still exists and remains linked from the quick view.

## Verification

- `pytest tests/test_api_products.py -q`
- `npm run build`
