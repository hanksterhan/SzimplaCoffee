# SC-46 - Normalized product metadata foundation

## What changed

- Added normalized metadata columns to `products` for origin country, origin region, roast level, process family, metadata confidence, and metadata source.
- Exposed those fields in backend product schemas so later catalog and deal work can use them directly.
- Added the repo's first Alembic scaffold and revision for backend schema changes.
- Extended the startup compatibility shim so older local SQLite databases can add the new columns safely on boot.
- Updated the metadata backfill script so it can populate the normalized fields and provenance from the existing parser.
- Documented the migration and backfill commands in `backend/README.md`.

## Why it changed

The product model was too dependent on free-text fields to support reliable faceting by country, roast, and process. This ticket establishes the canonical schema layer and a reproducible way to migrate and backfill it without removing the legacy text that still matters for audit and display.

## Notes / sharp edges

- Alembic is now the canonical schema migration path, but the bootstrap compatibility shim remains intentionally so older local databases do not break before every workflow adopts Alembic.
- Backend verification still spans two environments: `backend/.venv` for Alembic and the repo-root `.venv` for `pytest` and `ruff`.
- The parser-backed backfill is heuristic. It creates a usable migration path, not guaranteed perfect metadata.
- The repo still has no `stage` branch, so the delivery PR targets `main`.

## Verification

- `cd backend && .venv/bin/alembic upgrade head`
- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests scripts/backfill_product_metadata.py alembic`
- `rg -n 'origin_country|origin_region|roast_level|process_family|metadata_confidence|metadata_source' backend/src backend/alembic backend/scripts .plans/SC-46-execution-plan.md -S`
