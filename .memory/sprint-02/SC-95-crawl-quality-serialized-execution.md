# SC-95 — Crawl quality signals + serialized low-CPU batch execution

**Closed:** 2026-03-19T20:40:00Z

## What Changed

- `scheduler.py`: Added `DEFAULT_SCHEDULED_CRAWL_BATCH_SIZE = 1` constant enforcing one-at-a-time routine crawl execution. Added `RECENT_CRAWL_SIGNAL_WINDOW = 5`. Introduced `_get_recent_runs()` helper for efficient bulk fetch of recent CrawlRun history per merchant. Added `_sort_due_merchants()` for overdue-first priority ordering. Extended `get_merchants_due_for_crawl()` with optional `limit` param. Extended `get_crawl_schedule()` to return per-merchant reliability signals: `recent_run_count`, `recent_success_rate`, `recent_failure_count`, `last_completed_crawl_quality_score`, `latest_run_status`, `latest_error_summary`.
- `main.py`: `_run_scheduled_crawls()` now passes `limit=DEFAULT_SCHEDULED_CRAWL_BATCH_SIZE` — APScheduler's every-15-min job processes at most 1 merchant per tick, and logs total-due vs processed count.
- `api/crawl.py`: `CrawlScheduleItem` Pydantic model extended with reliability signal fields. `run_due_merchants` endpoint respects the same batch limit.
- `tests/test_scheduler.py`: 13 tests (all pass) covering tier constants, due detection, failed-run exclusion, batch limit proof (one merchant returned), and schedule reliability signal shape.

## Why It Changed

Phase 2 goal requires crawl quality to be observable and execution to be conservative. The previous scheduler would fan out all due merchants in a single tick with no batch cap, risking CPU overload. Now routine crawls are strictly serialized.

## Surprises / Notes

- The feature branch was already partially done from a prior session. The working tree had all the diffs unstaged — this run confirmed all tests pass, staged, committed, and merged.
- `crawl_quality_score` already existed on `CrawlRun` from SC-51. The new reliability signals reuse it directly.
- The `run_due_merchants` API endpoint also respects the batch limit, making manual triggers consistent with the scheduler.

## Follow-ups / Sharp Edges

- SC-96 is now unblocked: catalog filtering/search semantics aligned with normalized metadata.
- Increasing the batch size from 1 requires a policy change or explicit escalation — good.
- The schedule API now surfaces enough trust data for a future merchant trust dashboard.
