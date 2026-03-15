# SC-46 Execution Plan

## Scope

Introduce normalized coffee metadata fields and a safe migration path while preserving legacy free-text columns.

## Out of Scope

- Full-corpus backfill completion
- Catalog UI filters
- Deal intelligence

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && alembic upgrade head`
- AC-2 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-3 → `rg -n 'origin_country|roast_level|process_family|metadata_confidence|metadata_source' backend/src backend/alembic .plans -S`

## Slice Boundaries

### S1 Define normalized metadata schema and ORM fields
- Files create: `backend/alembic/versions/`
- Files modify: `backend/src/szimplacoffee/models.py`, `backend/src/szimplacoffee/schemas/products.py`
- Files read only: `backend/src/szimplacoffee/coffee_parser.py`
- Prohibited changes: do not remove original free-text fields

### S2 Document migration and backfill strategy
- Files modify: `backend/README.md`, `.plans/SC-46-execution-plan.md`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not imply full backfill if only schema groundwork exists

## Verification Commands

- `cd backend && . .venv/bin/activate && alembic upgrade head`
- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
