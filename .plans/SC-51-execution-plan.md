# SC-51 Execution Plan

## Scope

Refactor crawling into explicit layered strategies and add per-merchant crawl-quality scoring.

## Out of Scope

- Review UI
- Mass custom adapter buildout for all merchants
- Daily deal ranking

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-2 → `rg -n 'catalog_strategy|promo_strategy|shipping_strategy|metadata_strategy|success_rate|crawl_quality' backend/src -S`
- AC-3 → `cd backend && . .venv/bin/activate && pytest -q`

## Slice Boundaries

### S1 Make crawl strategy layers explicit
- Files modify: `backend/src/szimplacoffee/services/crawlers.py`, `backend/src/szimplacoffee/services/platforms.py`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not make agentic fallback a default-first path

### S2 Persist crawl-quality metrics and merchant strategy state
- Files modify: `backend/src/szimplacoffee/models.py`, `backend/src/szimplacoffee/api/merchants.py`, `backend/src/szimplacoffee/services/crawlers.py`
- Files read only: `backend/src/szimplacoffee/services/discovery.py`
- Prohibited changes: do not hide low-confidence merchants behind success-only views

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
- `rg -n 'catalog_strategy|promo_strategy|shipping_strategy|metadata_strategy|success_rate|crawl_quality' backend/src -S`
