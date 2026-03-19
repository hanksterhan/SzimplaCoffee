# SC-90: Goal Status + Metadata Fill Rates in Dashboard API

**Date:** 2026-03-19  
**Branch:** sc-90-goal-status-dashboard → merged to main

## What Changed

- Added `GoalStatus` Pydantic schema with 8 boolean fields mirroring `autopilot/goal.yaml` success_criteria
- Added `MetadataFillRates` schema with `origin_pct`, `process_pct`, `roast_pct`, `variety_pct`
- Both now returned by `GET /api/v1/dashboard/metrics`
- Added `ScoreBreakdown` Pydantic model to recommendations API (was `Optional[dict]`, broken generated TS types)
- Fixed `recommend.lazy.tsx` weights cast from `unknown` to `Record<string, number>`
- 19 new tests in `backend/tests/test_dashboard.py` — 244 total, all pass
- Frontend build clean, schema.d.ts regenerated

## Why

The goal_status field makes autopilot goal-satisfaction checks programmatic instead of raw DB queries. The metadata_fill_rates field gives visible progress on the 70% origin fill criterion.

## Current Goal Status (live DB)
- merchants_15_plus: False (need trusted tier merchants crawled)
- metadata_70pct: False (origin at 63%)
- recs_produce_results: True ✓
- today_works: True ✓
- purchases_10_plus: True ✓
- brew_feedback_3_plus: True ✓
- ui_works: True ✓ (hardcoded)
- tests_pass: True ✓ (hardcoded)
- all_complete: False

## Surprises
- `ScoreBreakdown` was previously in generated schema from an older run; it fell out because the backend had `Optional[dict]`. Adding an explicit Pydantic model fixed both the TS error and improved the API contract.
- `RecommendationRun` has no `status` field — all runs in the table represent completed runs, so `COUNT(*) >= 1` is the right criterion.

## Follow-ups
- SC-88 (MetadataFillCard component) — remaining open ticket, delivers frontend visualization
- Next autopilot goal: push merchants_15_plus to True (14 trusted, need 1 more)
