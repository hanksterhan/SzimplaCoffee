# SC-61 — Coffee Parser Audit: Delivery Memory

**Date:** 2026-03-18  
**Ticket:** SC-61  
**Sprint:** 02  
**Delivered by:** h6nk-bot

## What Was Done

Audited the coffee metadata pipeline to verify `coffee_parser.py` runs post-crawl and measured baseline fill rates across all 597 products.

## Key Findings

### 1. Parser Is Pre-Wired (AC-1 ✅)

`coffee_parser.py` was already wired into `crawlers.py` before this ticket. Evidence:
- `crawlers.py:28`: `from .coffee_parser import parse_coffee_metadata`
- `crawlers.py:411`: Called inside `_enrich_payload_with_parser()` during the product upsert loop
- Logic: parser fills gaps only when crawler heuristics didn't populate a field (structured descriptions take priority)

**No code changes needed for wiring.**

### 2. Baseline Fill Rates (AC-3 ✅)

Measured against 597 products from 7 merchants:

| Field | Filled | Total | Rate |
|-------|--------|-------|------|
| origin_text | 387 | 597 | **64.8%** |
| process_text | 203 | 597 | **34.0%** |
| roast_level (non-unknown) | 11 | 597 | **1.8%** |
| variety_text | 141 | 597 | **23.6%** |
| origin_country | 378 | 597 | **63.3%** |
| process_family (non-unknown) | 266 | 597 | **44.6%** |

### 3. Backfill-Metadata Returns 0 Updates (AC-2 ✅)

`szimpla backfill-metadata` runs cleanly but updates 0/597 products. Reasons:
1. Fields already populated at crawl time for products with names that contain origin/process keywords
2. **Critical**: `Product` model has **no `description_html` column**. Product descriptions are parsed at crawl time but not persisted in the database. The backfill command uses `getattr(product, "description_html", "") or ""` which returns `""` for all products. So backfill can only parse from product names — which yields nothing new since those same names were parsed at crawl time.

## Surprises / Failed Approaches

- S2 query used `WHERE origin IS NOT NULL` (column doesn't exist). Actual column is `origin_text`. The fields are: `origin_text`, `origin_country`, `origin_region`, `process_text`, `process_family`, `variety_text`, `roast_cues`, `roast_level`.
- Sprint planning context mentioned "93-95% empty" — that was stale data from 910 products. The current 597 products show much better rates (64.8% origin) because newer crawlers are more aggressive with structured fields.
- `roast_level` is still 98.2% unknown — this is the weakest field. Parser rules exist but most products don't explicitly state roast level in their name or description (which we're not storing anyway).

## Critical Info for SC-62/SC-63

1. **Descriptions are not in the DB.** The current backfill cannot use product descriptions — only names. Any regex improvement in SC-62/SC-63 that relies on description text will only take effect on future crawls (not backfill). If retroactive improvement is needed, descriptions must be added to the `products` table (migration required).

2. **Roast level is the urgent gap.** 1.8% fill rate vs 64.8% origin. The parser patterns exist but products rarely say "light roast" or "dark roast" in their names. SC-63 should consider inference: Ethiopian naturals → light, espresso blends → medium-dark, etc.

3. **Parser is non-destructive.** `_enrich_payload_with_parser()` only fills fields the crawler didn't populate. If a crawler sets `origin_text`, the parser doesn't override it. This means crawler-level extraction (Shopify tags, WooCommerce meta) takes priority.

4. **Process_family is derived, not direct.** `process_family` has 44.6% fill from the `_normalize_process_family()` function which converts `process_text` to a canonical family. Improving `process_text` extraction will automatically improve `process_family`.

## Follow-up Tickets

- **SC-62**: Improve parser regex patterns — roast level inference is highest ROI
- **SC-63**: Description storage decision — store `description_html` in Product to enable backfill

## Verification Passed

- 84 pytest tests: **PASS**
- ruff check: **PASS** (no changes were made to code)
