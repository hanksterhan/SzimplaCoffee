# SC-47 - Metadata extraction upgrade

## What changed

- Extended the coffee parser to emit normalized origin country/region, process family, roast level, and parser provenance alongside the existing free-text fields.
- Fixed the crawler coffee classifier so `filter` language no longer incorrectly excludes valid coffee products.
- Added merchant-level regex override patterns and product-level metadata override records to support explicit corrections with `override` provenance.
- Updated crawler enrichment and product upsert logic so normalized metadata, confidence, and source persist on products.
- Expanded parser tests to cover normalized outputs, override behavior, and the classifier regression.

## Why it changed

SC-46 added the normalized storage contract, but the ingestion layer still mostly produced free-text metadata. This ticket moves the parser and crawler onto that new contract so downstream filtering and review flows can rely on explicit normalized values and provenance.

## Notes / sharp edges

- Merchant regex overrides intentionally skip invalid regular expressions instead of failing the crawl.
- Product-level overrides currently match by external product id first, then exact product name.
- `structured` provenance is inferred from crawler-seeded text fields, so it reflects the current extraction path rather than a separate reviewed state.
- The repo still has no `stage` branch, so the delivery PR targets `main`.

## Verification

- `cd backend && ../.venv/bin/pytest tests/test_coffee_parser.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/services/coffee_parser.py src/szimplacoffee/services/crawlers.py src/szimplacoffee/models.py tests/test_coffee_parser.py`
- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- `rg -n 'override|metadata_source|metadata_confidence|merchant_field_patterns|product_metadata_overrides' backend/src backend/tests -S`
