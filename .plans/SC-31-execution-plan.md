# SC-31 Execution Plan: Wire Parser into Crawl Pipeline + Backfill

## Overview
Integrate the metadata parser (SC-30) into the crawl pipeline so every crawl extracts coffee metadata. Then backfill all 910 existing products.

## Pre-work
1. Verify SC-30 parser is complete and tested
2. Check if products store body_html in the DB or if re-fetch is needed
3. Review Product model for any missing columns (roast_level, altitude_text, varietal_text)

## Execution

### S4: Model fields (30 min)
- Check Product model for roast_level, altitude_text, varietal_text columns
- Add missing columns via ALTER TABLE or model update
- Verify model imports still work

### S1: Shopify crawl integration (1 hour)
- In `_shopify_upsert_product()` or equivalent, after creating/updating Product:
  - Call `parse_coffee_metadata(body_html)`
  - Map CoffeeMetadata fields to Product model fields
  - Only overwrite if parsed value is non-empty (don't blank out existing data)

### S2: WooCommerce crawl integration (1 hour)
- Same pattern as S1 for WooCommerce adapter
- WooCommerce uses `description` field instead of `body_html`

### S3: Backfill CLI command (1-2 hours)
- Add `backfill-metadata` command to cli.py
- Iterate all products in DB
- For Shopify products: use stored body_html if available, else re-fetch product JSON
- For WooCommerce: similar approach with description field
- Log stats: "Processed 910 products: 520 with origin, 380 with process, 650 with notes"
- Add API endpoint POST /api/v1/products/backfill-metadata for triggering from UI

## Verification
1. Run backfill: `python -m szimplacoffee.cli backfill-metadata`
2. Check stats: `SELECT COUNT(*) FROM products WHERE origin_text != ''` → should be >450
3. Crawl one merchant fresh, verify new products get metadata populated
4. Run recommendation engine, verify results now differentiate by origin/process
