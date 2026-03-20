# SC-101: Merchant Expansion — 10 New Merchants
_Completed: 2026-03-20_

## What Changed

Added 10 new merchants to the DB using `szimpla add-merchant` + `crawl_merchant()` calls.
Active merchant count: 16 → 26.

## Merchants Added

| Merchant | Platform | Products |
|----------|----------|----------|
| Equator Coffees | Shopify | 46 |
| Water Avenue Coffee | Shopify | 27 |
| Panther Coffee | Shopify | 24 |
| Methodical Coffee | Shopify | 43 |
| Press Coffee Roasters | Shopify | 159 |
| Batdorf & Bronson | Custom | 0 |
| Irving Farm New York | Shopify | 26 |
| Partners Coffee | Shopify | 44 |
| Novo Coffee | WooCommerce | 17 |
| Bold Bean Coffee Roasters | Shopify | 32 |

Total new products added: ~418. Total catalog: 1,341 products.

## Surprises / Issues

1. **`szimpla add-merchant` does not crawl by default** — need `--crawl-now` flag or
   call `crawl_merchant(db, merchant)` + `db.commit()` explicitly. Running without it
   leaves merchants with 0 products.

2. **`crawl_merchant` does not commit** — callers own the commit. When calling from
   an external script, always `db.commit()` after `crawl_merchant()`.

3. **Bot protection name mangling**: Equator Coffees' site returned "Something went wrong"
   as the HTML title during platform detection (Cloudflare bot check). The CLI trusted
   the title and stored it as the merchant name. Fixed via direct DB update. A future
   improvement would guard against obvious error-page titles in `_extract_name_from_html`.

4. **Batdorf & Bronson** is a custom platform with zero structured product data.
   It got Tier C. If it stays at 0 products after a few crawl cycles, it should be
   moved to Tier D or deactivated.

## Follow-ups / Sharp Edges

- All new Shopify/WooCommerce merchants should get re-crawled by APScheduler over the
  next 24h cycle now that they're Tier A.
- Press Coffee has a very large catalog (159 products) — worth checking metadata coverage
  after the next quality scorer run.
- Batdorf & Bronson needs a manual check or custom adapter before it contributes catalog data.
- Consider adding guard in `_extract_name_from_html` to reject titles that look like
  error pages (e.g., "Something went wrong", "Access denied", "Attention Required").

## Verification

- 290 backend tests passing
- score-merchants: 26 merchants scored without error
- 9/10 merchants have products (AC-1 ✅)
- Active count: 26 (AC-2 ✅)
- No Tier D merchants (AC-4 ✅)
