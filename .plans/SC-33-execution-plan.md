# SC-33 Execution Plan: Crawl Scheduler

## Overview
Tier-based crawl scheduling so data stays fresh and temporal trends emerge.

## Execution

### S1: Scheduler service (1.5 hours)
**Create:** `backend/src/szimplacoffee/services/scheduler.py`

```python
TIER_INTERVALS = {"A": 12, "B": 24, "C": 168}  # hours

def get_due_merchants(session) -> list[Merchant]:
    # For each merchant, find latest successful CrawlRun
    # If now - last_crawl > tier_interval, merchant is due
    # Return list sorted by priority (overdue first)

def run_scheduled_crawls(session) -> dict:
    # Get due merchants, crawl each, return summary
```

### S2: CLI commands (30 min)
- `crawl-schedule`: table of merchant | tier | last_crawl | next_due | status
- `run-scheduled-crawls`: execute all due crawls, print results

### S3: API endpoints (30 min)
- GET /api/v1/crawl-schedule → list of merchants with schedule info
- POST /api/v1/crawl-schedule/run → trigger all due crawls

### S4: Dashboard freshness indicator (1 hour)
- Show data freshness on dashboard: "Last crawl: 3h ago" or "⚠️ Stale: 48h since last crawl"
- Color-coded: green (<interval), yellow (approaching), red (overdue)

## Cron Setup (docs only)
```
# Every 6 hours, run scheduled crawls
0 */6 * * * cd /path/to/SzimplaCoffee && python -m szimplacoffee.cli run-scheduled-crawls >> /var/log/szimplacoffee-crawl.log 2>&1
```

## Verification
1. Run schedule check: `python -m szimplacoffee.cli crawl-schedule`
2. Run scheduled crawls: `python -m szimplacoffee.cli run-scheduled-crawls`
3. Wait, run again — should skip recently crawled merchants
4. After a few days, verify offer_snapshots has multiple distinct dates
