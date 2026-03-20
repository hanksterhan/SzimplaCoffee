# SC-111 Merchant Expansion Batch 3

## What changed
- Imported 10 new merchant records from the seed list in a serialized batch to avoid CPU spikes.
- Successfully crawled 8 newly added merchants that produced products:
  - Temple Coffee Roasters — 45 products
  - ReAnimator Coffee — 17 products
  - Barista Parlor — 1 product
  - Alana's Coffee Roasters — 33 products
  - Conduit Coffee — 9 products
  - Cuvée Coffee — 23 products
  - Broadsheet Coffee Roasters — 13 products
  - Four Barrel Coffee — 30 products
- Active merchant count increased from 36 to 48.

## Verification
- `cd backend && . .venv/bin/activate && pytest tests/ -q` → 345 passed
- `cd backend && . .venv/bin/activate && ~/.local/bin/ruff check src/ tests/` → passed

## Failures / surprises
- Seed list contained at least one stale URL: `broadsheetcoffeeroasters.com` did not resolve; corrected live to `broadsheetcoffee.com`.
- `compellingandrich.com` and `exoroast.com` returned NXDOMAIN.
- `sycamorecoffee.com` detected as unknown platform and produced 0 products.
- `thirdrailcoffee.com` failed SSL hostname verification.
- `lighthousecoffee.com` timed out during connect.
- `baristaparlor.com` only produced 1 product, which appears to reflect current shop breadth rather than a crawler crash.

## Why it changed
- SC-111 expands merchant coverage to improve recommendation diversity and deal discovery while keeping crawl execution serialized per autopilot policy.

## Follow-ups
- SC-116 can use the stale/failing domains above as avoid-or-verify-first candidates.
- Seed list should be refreshed opportunistically to replace dead domains and known SSL-problem merchants.
