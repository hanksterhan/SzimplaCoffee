# SC-50 — Recurring Crawl Scheduling

## What changed

- **`backend/src/szimplacoffee/main.py`**: Added APScheduler `BackgroundScheduler` that starts on app lifespan and runs `_run_scheduled_crawls` every 15 minutes. The job calls `get_merchants_due_for_crawl` and executes `crawl_merchant` per-merchant with a `CrawlRun` record. Per-merchant errors are caught so one failure doesn't abort the batch.
- **`backend/tests/test_scheduler.py`**: New test file covering tier intervals, due-detection logic (never-crawled, fresh, overdue), tier-D exclusion, inactive merchant exclusion, and failed-run not resetting freshness clock. 11 tests added.
- **`backend/README.md`**: New section documenting scheduler operation, tier thresholds, observability endpoints, and the minimum history required before daily-sales data is trustworthy.
- **`README.md`**: Added "Recurring Crawl Scheduling" section with tier table and API endpoints.

## Why

The app had a full crawl infrastructure (`CrawlRun`, `get_merchants_due_for_crawl`, `crawl_merchant`) but no recurring execution. Without scheduled crawls, no offer history could accumulate and daily-sales detection was meaningless.

## Surprises / notes

- APScheduler 3.x (`BackgroundScheduler`) integrates cleanly with FastAPI lifespan context manager.
- The scheduler runs every 15 minutes but per-merchant tier thresholds mean most merchants are not crawled on every tick. Tier A gets crawled at most every 6 hours.
- `global _scheduler` + `daemon=True` ensures clean shutdown when the process exits.

## Verification

```
cd backend && . .venv/bin/activate && pytest -q        # 63 passed
cd backend && . .venv/bin/activate && ruff check src tests  # clean
bash -lc "test -f backend/src/szimplacoffee/scheduler.py && echo OK"  # OK
```
