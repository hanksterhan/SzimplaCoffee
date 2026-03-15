# SC-47 Execution Plan

## Scope

Upgrade metadata extraction so normalized fields are filled with confidence scores, provenance, and override support.

## Out of Scope

- Review UI for agentic extractions
- Full 500-merchant rollout
- Deal-scoring logic

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest tests/test_coffee_parser.py -q`
- AC-2 → `rg -n 'override|metadata_source|metadata_confidence|merchant_field_patterns|product_metadata_overrides' backend/src backend/tests -S`
- AC-3 → `cd backend && . .venv/bin/activate && pytest tests/test_coffee_parser.py -q`

## Slice Boundaries

### S1 Normalize extraction dictionaries and confidence scoring
- Files modify: `backend/src/szimplacoffee/coffee_parser.py`, `backend/src/szimplacoffee/services/crawlers.py`, `backend/tests/test_coffee_parser.py`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not leave the filter-positive contradiction unresolved

### S2 Add override and provenance plumbing
- Files modify: `backend/src/szimplacoffee/models.py`, `backend/src/szimplacoffee/services/crawlers.py`, `backend/src/szimplacoffee/bootstrap.py`
- Files read only: `backend/src/szimplacoffee/schemas/products.py`
- Prohibited changes: do not silently overwrite without provenance

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest tests/test_coffee_parser.py -q`
- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
