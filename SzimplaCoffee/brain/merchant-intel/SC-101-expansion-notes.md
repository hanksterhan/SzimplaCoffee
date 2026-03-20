# SC-101 Merchant Expansion Notes
_Added 2026-03-19 — 10 new merchants imported_

## Crawl Results Summary

| Merchant | Domain | Platform | Products | Notes |
|----------|--------|----------|----------|-------|
| Equator Coffees | equatorcoffees.com | Shopify | 46 | Bot-protection returned "Something went wrong" title during platform detection — name fixed manually. Products crawled OK on second pass. |
| Water Avenue Coffee | wateravenuecoffee.com | Shopify | 27 | Clean Shopify crawl. |
| Panther Coffee | panthercoffee.com | Shopify | 24 | Named "PantherCoffee" in Shopify config — Miami-based, strong espresso program. |
| Methodical Coffee | methodicalcoffee.com | Shopify | 43 | Clean crawl. Greenville SC. |
| Press Coffee Roasters | presscoffee.com | Shopify | 159 | Large catalog (1607 records written) — many variants. Phoenix AZ. |
| Batdorf & Bronson | batdorfcoffee.com | Custom | 0 | Custom platform, no structured data extracted. Tier C. May need agentic fallback or manual import. |
| Irving Farm New York | irvingfarm.com | Shopify | 26 | Clean crawl. NYC/Hudson Valley. |
| Partners Coffee | partnerscoffee.com | Shopify | 44 | Clean crawl. NYC. |
| Novo Coffee | novocoffee.com | WooCommerce | 17 | WooCommerce. Denver. |
| Bold Bean Coffee Roasters | boldbeancoffee.com | Shopify | 32 | Clean crawl. Jacksonville FL. |

## Issues Noted

1. **Equator Coffees name mangling**: Platform detection hit Cloudflare bot protection and
   returned page title "Something went wrong" as the merchant name. The CLI `add-merchant`
   command trusts HTML title unconditionally. Name was fixed via direct DB update after import.
   Future improvement: validate that detected name doesn't look like an error page title.

2. **Batdorf & Bronson (custom)**: Zero products. Custom platform with no Shopify/WooCommerce
   structured data. Not worth spending crawl cycles on until a custom adapter is available.
   Candidate for `is_active=False` or Tier D if it doesn't produce data after a few scheduler ticks.

3. **`crawl_merchant` session ownership**: The function does not call `session.commit()` —
   callers must commit. The CLI (`szimpla add-merchant --crawl-now`) commits via the session
   context manager. When calling from scripts, always commit after `crawl_merchant()`.

## All ACs Met
- 9/10 merchants have products (≥8 required) ✅
- Active merchant count: 26 (≥24 required) ✅
- score-merchants ran clean, scored 26 merchants ✅
- No new Tier D merchants (batdorf is Tier C) ✅
