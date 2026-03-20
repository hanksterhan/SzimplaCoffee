# SC-104 Execution Plan

## Goal

Persist product description text from crawlers and use it during metadata backfill so origin/process extraction can move past title-only limits.

## Context

Origin coverage is structurally capped because only product titles are stored. Shopify/WooCommerce product payloads often include richer descriptions that contain origin and process details.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/models.py`
- `backend/migrations/versions/*`
- `backend/src/szimplacoffee/services/crawlers.py`
- `backend/src/szimplacoffee/services/coffee_parser.py`
- `backend/src/szimplacoffee/cli.py`
- related backend tests

## Implementation Steps

1. Add nullable `description_text` to `Product` and create/apply migration.
2. Extract and strip description text from crawler responses into `description_text`.
3. Extend parser/backfill code to use `description_text` as a secondary signal source.
4. Add focused tests around description-driven extraction.
5. Run live `backfill-metadata` and measure fill-rate improvements.

## Risks / Notes

- Schema migration requires careful verification.
- Keep stored text bounded and normalized; do not persist raw HTML.
- Product description availability may differ between platforms.

## Verification

- `cd backend && pytest tests/test_coffee_parser.py -q`
- `cd backend && pytest tests/ -q`
- `cd backend && ~/.local/bin/ruff check src/ tests/`
- `cd backend && . .venv/bin/activate && szimpla backfill-metadata`

## Out of Scope

- Frontend display of description text
- Raw HTML storage
- Recommendation logic changes
