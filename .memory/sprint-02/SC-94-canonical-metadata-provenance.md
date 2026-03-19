# SC-94 — canonical metadata provenance

## What changed

- Added field-level canonical metadata confidence/source columns for `origin_country`, `process_family`, and `roast_level` on `Product` and `ProductMetadataOverride`.
- Extended `ParsedCoffeeMetadata` so the parser emits per-field confidence and provenance instead of only aggregate metadata confidence.
- Updated crawler enrichment/override application to preserve canonical metadata values together with field-level provenance and to recompute aggregate `metadata_confidence` / `metadata_source` from the strongest normalized field.
- Exposed a `canonical_metadata` API shape in product schemas so downstream catalog work can distinguish trusted normalized values from raw free text.
- Added regression coverage for parser provenance, payload enrichment, override precedence, and product API exposure.

## Why it changed

Phase 2 needs metadata trust, not just parser-best-effort strings. SC-94 makes normalized metadata legible enough for later filtering and ranking work by persisting both the canonical values and where/how confidently they were derived.

## Verification

- `cd backend && . .venv/bin/activate && pytest tests/test_coffee_parser.py tests/test_api_products.py -q` → 127 passed
- `cd backend && . .venv/bin/activate && pytest tests/ -q` → 247 passed
- Representative parser check via `parse_coffee_metadata(...)` confirmed field-level confidence/source output for Ethiopia washed light-roast and Brazil/Colombia blend medium-dark examples.

## Notes / sharp edges

- The aggregate parser `confidence` score is still a separate heuristic from the per-field confidence values; downstream consumers should prefer the new field-level metadata when evaluating trust for specific filters.
- A direct `_enrich_payload_with_parser` one-liner import triggered an existing circular-import path through `db.py`/`bootstrap.py`, so representative verification used `parse_coffee_metadata` directly instead of that helper.
- The repo was already carrying the SC-94 code diff in the workspace when this autopilot cycle began; this run verified the implementation and closed the ticket rather than generating a fresh diff from scratch.

## Follow-up

- SC-95 can now build crawl-quality trust on top of explicit normalized metadata provenance.
- SC-96 can use `canonical_metadata` for truthful catalog filtering once crawl trust work lands.
