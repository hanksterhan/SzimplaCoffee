# SC-31/32/33: CLI commands for metadata backfill, quality scoring, and crawl scheduling

**Date**: 2026-03-15  
**Tickets**: SC-31, SC-32, SC-33  
**Branch**: feature/SC-31-32-33-cli-gaps  
**PR**: https://github.com/hanksterhan/SzimplaCoffee/pull/8  
**Commit**: c8cf74e  

## What Changed

Three tickets had their core services/APIs already delivered in prior commits but were missing their CLI surface.

### SC-31 (backfill-metadata)
- `szimpla backfill-metadata` subcommand added to `cli.py`
- Re-runs `parse_coffee_metadata()` over all products, fills empty fields (origin, process, variety, tasting notes, country, region, process_family, roast_level)
- Prints per-field update counts and percentages
- Core services were already in place: `_enrich_payload_with_parser()` wired into Shopify, WooCommerce, and agentic crawl adapters in commit 1eccdb7

### SC-32 (score-merchants)
- `szimpla score-merchants` subcommand added — calls `score_all_merchants()` and displays ranked table
- `crawl_merchant()` in `crawlers.py` now auto-invokes `score_merchant()` after each successful crawl (wrapped in try/except so scoring failure cannot break crawl)
- Core service `quality_scorer.py` (271 lines) and API endpoint `/merchants/{id}/refresh-quality` were already delivered in commit 96f24ca

### SC-33 (crawl-schedule / run-scheduled-crawls)
- `szimpla crawl-schedule` — shows table of all merchants with tier, interval, last crawl, next due time, and DUE/ok status
- `szimpla run-scheduled-crawls` — crawls all merchants whose tier interval has elapsed
- Core service `scheduler.py` (129 lines) and API endpoints (`/crawl/schedule`, `/crawl/due`, `/crawl/run-due`) were already delivered in commit 96f24ca; APScheduler in `main.py` handles automatic background scheduling

## Verification
- `pytest tests/ -q` — 72 passed
- `uvx ruff check src tests` — all checks passed
- `npx tsc -b` — clean

## Notes for Future Sessions
- The CLI commands require the SQLite database to be accessible. When running `szimpla` from a shell, ensure `DATABASE_PATH` env var is set or the default `data/szimplacoffee.db` exists.
- Quality scoring is now side-effecting on every crawl. If the scorer develops a bug, it is safely wrapped, but quality profiles will silently not update. Monitor via `szimpla score-merchants` output.
- Draft tickets SC-45, SC-52, SC-53 remain in `.tickets/open/` as drafts — not ready for delivery.
