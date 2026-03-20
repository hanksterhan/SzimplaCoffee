# SC-105 — Merchant expansion: 10 new merchants

**Delivered:** 2026-03-20T07:15:00Z

## What Changed

10 new merchants imported via `szimpla add-merchant <url> --crawl-now` one at a time.

### Merchants Added
| Merchant | Domain | Platform | Products | Tier |
|---|---|---|---|---|
| Elixr Coffee | elixrcoffee.com | Shopify | 9 | A |
| Dark Matter Coffee | darkmattercoffee.com | Shopify | 31 | A |
| Crema Coffee Roasters | cremacoffeeroasters.com | Shopify | 21 | A |
| Greater Goods Roasting | greatergoodscoffee.com | Shopify | 23 | A |
| Cartel Roasting Co. | cartelcoffeelab.com | WooCommerce | 19 | A |
| Presta Coffee | prestacoffee.com | Shopify | 12 | A |
| Tandem Coffee Roasters | tandemcoffee.com | Shopify | 103 | A |
| Tobys Estate Coffee USA | tobysestate.com | Custom | 0 | C |
| Parlor Coffee | parlorcoffee.com | Shopify | 28 | A |
| Birch Coffee | birchcoffee.com | Shopify | 29 | A |

- Active merchant count: 26 → 36
- Products from new merchants: ~275 new catalog entries
- 9 of 10 have products (Toby's Estate is custom platform → 0 products as expected)

## Candidate Selection Process

- URL-verified with curl before import (broadsheetcoffeeroasters.com, exoroast.com, compellingandrich.com returned 000/unreachable → skipped)
- Selected 10 Tier B espresso-relevant US roasters from seed list
- Ran imports fully serialized per CPU guardrail policy

## Surprises

- Tandem Coffee Roasters had 103 products (more than any other merchant) — may include accessories/gear
- Toby's Estate detected as `custom` platform; 0 products, scored tier C. Expected outcome.
- Cartel was WooCommerce, not Shopify as listed in seed (auto-detection worked fine)

## score-merchants Results

Top new additions by overall score:
- Elixr Coffee: 0.53 overall
- Dark Matter Coffee: 0.49 overall (espresso score 0.58 — high)
- Crema Coffee Roasters: 0.47 overall

## Verification

- 298 backend tests pass (no regressions)
- score-merchants completed cleanly for all 36 merchants

## Follow-ups

- Tandem's 103 products should be reviewed — high count could mean non-coffee items inflating the catalog
- Dark Matter has espresso_score=0.58 which is the highest of any new merchant; good candidate for recommendations
- Toby's Estate (custom) is effectively Tier D; could be excluded from future runs or left as inactive placeholder
