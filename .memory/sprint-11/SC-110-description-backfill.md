# SC-110 — Description backfill re-pass

Date: 2026-03-20
Ticket: SC-110

## What changed

- Added a new backend CLI command: `szimpla backfill-descriptions`
- The new command performs two bounded passes over active products:
  1. Re-classifies obvious non-coffee products from parser signals, even when they were still stored as `product_category=coffee`
  2. Re-runs metadata parsing for products with `description_text` and upgrades metadata only when the description-backed parse has higher confidence than the stored value
- Added backend regression coverage in `backend/tests/test_backfill_descriptions.py`

## Why it changed

The existing `backfill-metadata` command already parsed `description_text`, but it was primarily an empty-field fill pass. The live catalog had recently-crawled products that were still misclassified as coffee even though the parser clearly recognized them as filters, pins, vinyl, gift subscriptions, and other non-coffee items. That inflated the denominator for catalog trust metrics.

SC-110 adds a targeted re-pass that improves the trustworthy denominator and upgrades metadata conservatively.

## Live verification notes

Running `szimpla backfill-descriptions` on the live DB produced:

- Updated: 69 / 1613 active products
- Reclassified as non-coffee: 48
- Origin upgrades: 0
- Roast upgrades: 0
- Process upgrades: 21

Fill-rate summary on all active products stayed roughly flat for origin (`906/1613 = 56.2%`), but the meaningful coffee-only origin coverage improved because obvious non-coffee rows were removed from the coffee denominator.

Post-run counts:

- Coffee products: 1371
- Non-coffee products: 242
- Origin coverage on coffee products: `851 / 1371 = 62.1%`

## Important finding

Description-only re-pass did **not** materially improve `origin_country` fill on the current dataset. The main reason is structural:

- most products missing origin still have no `description_text`, or
- their descriptions do not contain usable country signals

So the next real path to origin improvement is richer crawl text / structured extraction, not another blind re-pass.

## Follow-ups / sharp edges

- SC-111 merchant expansion remains the next best unblocked task
- If origin coverage needs a larger jump, future work should focus on crawl/adapter fidelity or targeted merchant-specific field patterns rather than repeated parser reruns
