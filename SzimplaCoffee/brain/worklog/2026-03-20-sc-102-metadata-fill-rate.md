# 2026-03-20 — SC-102 metadata fill rate

## Summary

Delivered SC-102 by tightening parser classification and running two metadata backfill passes.

## What changed

- Expanded non-coffee detection for gear, merch, and non-roasted beverage products.
- Fixed ambiguous `Java` / `Congo` country-token handling.
- Improved roast fallback for specialty single-origin naming patterns.
- Added low-confidence `country-default` process inference in backfill when explicit process text is absent but origin is known.

## Result

Active-product fill rates moved from:
- roast unknown: 259 / 919 (28.2%) → 175 / 919 (19.0%)
- process unknown: 451 / 919 (49.1%) → 233 / 919 (25.4%)

Also tagged 155 active products as `non-coffee`.

## Verification

- 152 parser tests passed
- 290 backend tests passed
- frontend build passed
- ruff passed

## Follow-up

Origin coverage remains the main remaining metadata gap because descriptions are not persisted. A future ticket should improve origin fill using richer crawl text or stored description_html.
