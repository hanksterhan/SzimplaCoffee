# SC-102 — Metadata fill rate

## What changed

- Expanded the coffee parser’s non-coffee classifier to catch more equipment, merch, and non-roasted beverage products (for example Kalita gear, frothers, enamel pins, beanies, cascara/tea/latte/concentrate items).
- Added parser regression tests for:
  - non-coffee classification
  - specialty single-origin roast fallback behavior
  - ambiguous `Congo` / `Java` country-token handling
  - conservative country-level process defaults
- Fixed ambiguous country handling so `Java` is only treated as origin when no stronger country match exists, and `Congo` no longer creates false multi-origin matches inside names like `El Congo`.
- Improved roast inference so specialty single-origin cues (farm/estate naming, single-origin phrasing, explicit process-led lot naming) default to `light` when no explicit roast cue is present.
- Updated `backfill-metadata` so confirmed non-coffee products are tagged `product_category=non-coffee` and skipped for parser normalization writes.
- Added a conservative `country-default` process fallback in backfill for products that already have an origin country but no explicit process text. This writes low-confidence process semantics with explicit provenance instead of pretending parser certainty.
- Cleared a pre-existing unused import in `backend/src/szimplacoffee/api/products.py` found by lint.

## Before / after

Measured on active products:

- Before:
  - roast_unknown = 259 / 919 = 28.2%
  - process_unknown = 451 / 919 = 49.1%
  - origin_null = 343 / 919 = 37.3%
- After:
  - roast_unknown = 175 / 919 = 19.0%
  - process_unknown = 233 / 919 = 25.4%
  - origin_null = 343 / 919 = 37.3%
  - non_coffee tagged = 155

Measured on active coffee-only products (`product_category != non-coffee`):

- roast_unknown = 85 / 764 = 11.1%
- process_unknown = 132 / 764 = 17.3%
- origin_null = 233 / 764 = 30.5%

## Why this shape

The real blockers were not just missing parser patterns. A large share of `unknown` rows were active non-coffee products, and another large share were single-origin specialty coffees with origin already known in the DB but no explicit process text in the stored name field. Because descriptions are not persisted, a second-pass backfill heuristic was the smallest viable lever.

The process fallback is intentionally conservative and low-confidence. It is only used when the parser still has no explicit process and the product already has a country strong enough to justify a specialty-export default. Provenance is set to `country-default` so future work can distinguish this from parser-extracted truth.

## Verification

- `cd backend && . .venv/bin/activate && pytest tests/test_coffee_parser.py -q` → 152 passed
- `cd backend && . .venv/bin/activate && python -m szimplacoffee.cli backfill-metadata` → completed
- `cd backend && . .venv/bin/activate && pytest tests/ -q` → 290 passed
- `cd frontend && npm run build` → passed
- `cd backend && ~/.local/bin/ruff check src/ tests/` → passed

## Sharp edges / follow-ups

- Origin coverage did not improve here because product descriptions still are not stored; origin remains capped by what can be recovered from names and existing DB fields.
- Ethiopia was intentionally left out of country-default process inference because washed vs natural is too mixed to safely default.
- `country-default` process semantics are useful for trust-improvement, but Phase 2/3 should still prefer richer crawl text storage so these defaults can be replaced with explicit provenance where available.
