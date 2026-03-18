# SC-75 Execution Plan

## Goal
Crawl merchants 8-12 (Blue Bottle, Stumptown, Heart, George Howell, Passenger) and verify product ingestion.

## Context
Part 2 of a 3-batch crawl split to keep each autopilot run manageable. Merchants were imported in SC-57. SC-58 crawled merchants 3-7.

## Files / Areas Expected to Change
- `data/szimplacoffee.db` — crawl_runs and products rows added
- No source code changes expected

## Implementation Steps
1. Activate backend venv: `cd backend && source .venv/bin/activate`
2. Check pre-crawl product count: `szimpla crawl-schedule` to confirm merchants 8-12 are registered
3. Run crawls for each merchant by ID or use `szimpla crawl-all` (scheduler will pick up all due merchants)
4. Verify crawl_runs rows: query `SELECT merchant_id, status FROM crawl_runs WHERE merchant_id BETWEEN 8 AND 12`
5. Verify product count increased
6. Document any failures with their error messages in delivery notes

## Risks / Notes
- Blue Bottle (merchant 8) uses a custom platform — likely to fail adapter detection
- Stumptown is Nestlé-owned, site may have anti-scraping protections
- Heart and Passenger are standard Shopify — should work cleanly
- Failures are expected and acceptable; the goal is documentation, not 100% success

## Verification
- `pytest tests/ -q` — all existing tests pass
- `ruff check src/ tests/` — no lint errors
- Query confirms crawl_runs rows for merchants 8-12

## Out of Scope
- Fixing failed crawl adapters
- Metadata parsing
- Trust tier promotion
