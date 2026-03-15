# SC-50 Execution Plan

## Scope

Start recurring crawl scheduling so the app can accumulate real historical offer data over time.

## Out of Scope

- Distributed work queues
- Cloud automation
- 500-merchant tuning

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-2 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-3 → `rg -n 'scheduler|recurring crawl|APScheduler|startup' backend README.md .plans -S`

## Slice Boundaries

### S1 Wire scheduler loop to real crawl execution
- Files modify: `backend/src/szimplacoffee/main.py`, `backend/src/szimplacoffee/scheduler.py`, `backend/src/szimplacoffee/crawl.py`
- Files read only: `backend/src/szimplacoffee/models.py`
- Prohibited changes: do not assume a hidden external daemon

### S2 Document scheduler operation and freshness expectations
- Files modify: `README.md`, `backend/README.md`
- Files read only: `backend/src/szimplacoffee/scheduler.py`
- Prohibited changes: do not claim trustworthy deal history before enough days have accrued

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
- `rg -n 'scheduler|recurring crawl|APScheduler|startup' backend README.md .plans -S`
