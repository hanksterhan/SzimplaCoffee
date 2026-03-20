# SC-104: Persist description_text for richer metadata extraction

**Delivered:** 2026-03-20  
**Branch merged:** sc-104-description-text → stage  
**Tests:** 298 passed (294 existing + 4 new SC-104 parser tests)

## What Changed

### Schema
- Added `description_text: Optional[str]` nullable TEXT column to `Product` model
- Alembic migration: `20260320_01_sc104_add_description_text_to_products`
- Migration applied cleanly to live DB

### Shopify Crawler
- Extracts `body_html` via `_clean_text()` and stores first 2000 chars as `description_text`
- `_upsert_product()` now writes `description_text` from payload when present

### WooCommerce Crawler
- Extracts `raw.get("description", "")` via `_clean_text()` and stores first 2000 chars
- Same `_upsert_product()` path handles persistence

### CLI backfill-metadata
- Fixed: was calling `getattr(product, "description_html", "")` — field never existed, always returned `""`
- Now correctly calls `product.description_text or ""`
- Backfill result: 91 active products improved (process_family, roast_level, product_category)

### Tests Added
- `test_sc104_parser_uses_description_for_origin` — "Mystery Coffee" → Ethiopia from description
- `test_sc104_parser_uses_description_for_process` — Guatemala + "Process: Natural" → natural
- `test_sc104_parser_uses_description_for_roast` — Guatemala + "Roast level: light" → light
- `test_sc104_parser_empty_description_graceful` — no crash on empty description

## Fill Rate Baseline (post-backfill, pre-recrawl)

Active coffee products: 1144  
- origin_country: 772/1144 = 67%  
- process_family (non-unknown): 937/1144 = 81%  
- roast_level (non-unknown): 1029/1144 = 89%  

Note: description_text is null for all existing products (populated on next crawl pass). The 67% origin fill is a pre-recrawl baseline. AC-5 target of ≥70% will be measurable after next full crawl.

## Surprises / Failures

- The CLI backfill had been silently using `getattr(product, "description_html", "") or ""` which always returned `""`. This means every backfill run since SC-94 was parser-running without description signal. Fixed.
- Alembic `autogenerate` failed with missing `script.py.mako` template — wrote migration manually. This is consistent with the repo pattern (previous migrations were also hand-written).

## Follow-ups

- AC-5 (≥70% origin fill) will verify on next crawl pass after merchants re-crawl and populate description_text
- WooCommerce products: description comes from `raw.get("description")` in store API; typically short structured text; should yield useful origin/process signals
- Consider a separate ticket to track: after 1 full crawl cycle with description_text, measure fill rate delta
