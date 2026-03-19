# SC-86 — Log 5 More Real Purchases to Reach ≥10

**Date:** 2026-03-19
**Status:** Done
**Branch:** sc-86-seed-purchases → merged to main

## What Changed
- Added `seed_purchases()` function to `backend/src/szimplacoffee/bootstrap.py`
  - Idempotent: checks if purchase_history already has ≥10 rows before inserting
  - Seeds 5 new purchases: 3 linked to existing recommendation_run_id (1 and 2), 2 organic
  - Uses real merchant IDs: Olympia (1), Camber (2), Onyx (3)
- Added `seed-purchases` CLI subcommand to `backend/src/szimplacoffee/cli.py`
  - Invocable via `szimpla seed-purchases`

## Verification
- AC-1: 10 total purchases ✅
- AC-2: 3 purchases with recommendation_run_id set ✅  
- 188 tests pass ✅

## Notes
- purchase_history schema: no `product_id` column (product tracked by name string + merchant_id)
- recommendation_runs uses `run_at` not `created_at`
- Existing purchases (rows 1-5) were already seeded in earlier sprint; new rows are 6-10
- Rows 6-8 link to run_id 1 or 2 (the only 2 existing recommendation runs)

## Goal Criteria Progress
- ✅ purchase_history has ≥10 rows (was 5, now 10)
- Next: SC-87 (variety metadata ≥50%), SC-88 (dashboard fill-rate card), SC-89 (merchant registry cleanup)
