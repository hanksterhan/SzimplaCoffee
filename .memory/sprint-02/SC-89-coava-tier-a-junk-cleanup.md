# SC-89 — Promote Coava to Tier A, Deactivate Junk Tier-D Merchants

**Date:** 2026-03-19  
**Ticket:** SC-89  
**Status:** done

## What Changed

- Added `fix-merchant-registry` CLI subcommand to `backend/src/szimplacoffee/cli.py`
- Coava Coffee Roasters: `crawl_tier C→A`, `trust_tier candidate→trusted`
- Blue Bottle Coffee, Stumptownroasters, Not A Url: `is_active=False` (deactivated, not deleted)
- 4 new tests in `backend/tests/test_fix_merchant_registry.py`
- 225 total tests passing (was 221)

## Why

Coava had a successful crawl (1 product, `confidence=0.55`) and is a legitimate specialty roaster. Its Tier C assignment prevented it from appearing in recommendations. Promoting to Tier A makes it eligible for 6h crawl cadence and recommendation inclusion.

The 3 Tier-D rows were garbage: a failed URL ("Not A Url"), a domain duplicate (Stumptownroasters vs Stumptown Coffee), and a merchant that belongs to a competitor product catalog (Blue Bottle Coffee). These skewed registry counts and could mislead recommendations.

## Approach

Chose `is_active=False` (deactivate) rather than hard DELETE to preserve referential integrity with existing `crawl_runs` rows. Blue Bottle had 1 crawl_run row; deleting would cause FK violation without cascade.

Applied via a new CLI command rather than a one-off migration script — more reproducible and testable.

## Goal Progress

After this change: 14 active Tier-A merchants. Goal criteria `merchants_15_plus` is now at 14/15 — one more Tier-A promotion or import closes it.

## Surprises

- The CLI `is_active == True` comparison (using `==`) produces incorrect COUNT in SQLAlchemy ORM with SQLite booleans. Fixed to use `.is_(True)` in the summary and test queries.
- `completed_at` column doesn't exist on `crawl_runs` — it's `finished_at`.

## Follow-ups

- Crawl Coava again soon; current catalog is only 1 product.
- Import 1 more merchant to hit 15 active Tier-A threshold for goal criterion.
