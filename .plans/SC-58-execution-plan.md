# SC-58 Execution Plan

## Goal
Crawl the first 5 Tier A merchants (Onyx, Intelligentsia, Counter Culture, Verve, Sightglass) and verify product ingestion.

## Context
Part 1 of a 3-batch crawl split. Batch 2: SC-75 (merchants 8-12). Batch 3: SC-76 (merchants 13-15).
Merchants were imported in SC-57.

## Files / Areas Expected to Change
- `data/szimplacoffee.db` — crawl_runs and products rows added
- No source code changes expected

## Implementation Steps
1. Activate backend venv: `cd backend && source .venv/bin/activate`
2. Check pre-crawl product count baseline
3. Run crawls for merchants 3-7 (`szimpla crawl-all` or individual merchant crawl triggers)
4. Verify crawl_runs rows: `SELECT merchant_id, status FROM crawl_runs WHERE merchant_id BETWEEN 3 AND 7`
5. Verify product count increased
6. Document any failures in delivery notes

## Risks / Notes
- All 5 merchants are Tier A Shopify — low risk of adapter failure
- Intelligentsia has a large catalog — crawl may take a few minutes
- If crawl-all triggers all merchants (including 1 and 2), that is fine — Olympia and Camber will just get refreshed

## Verification
- `pytest tests/ -q`
- `ruff check src/ tests/`
- Query confirms crawl_runs rows for merchants 3-7

## Out of Scope
- Merchants 8-15 (SC-75 and SC-76)
- Fixing failed adapters
- Metadata parsing
