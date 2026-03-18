# SC-58 Delivery Memory — Crawl Batch 1 (Tier A Anchors)

**Date:** 2026-03-18  
**Ticket:** SC-58  
**Sprint:** 02

## What Changed

Crawled 5 Tier A merchants (IDs 3-7) using the Shopify JSON feed adapter:

| Merchant | Records Written | DB Products | Confidence |
|---|---|---|---|
| Onyx Coffee Lab | 601 | 132 | 0.95 |
| Intelligentsia Coffee | 460 | 168 | 0.95 |
| Counter Culture Coffee | 386 | 146 | 0.95 |
| Verve Coffee Roasters | 814 | 93 | 0.95 |
| Sightglass Coffee | 325 | 20 | 0.95 |

- **Products before:** 38 (Olympia + Camber from prior crawls)
- **Products after:** 597 (net +559 new coffee SKUs)
- **Crawl runs added:** 5 (total crawl_runs: 7)
- All crawls used Shopify feed adapter with confidence=0.95

## Why

These are the top-quality Tier A merchants — the most important anchors for the recommendation engine. No product data existed for them before this ticket.

## Surprises / Notes

- `records_written` in crawl summary includes all Shopify product variants (hence higher numbers), while DB products count only deduplicated parent products
- Column name was `confidence` not `confidence_score` in crawl_runs table (corrected during verification)
- `ruff` is not in the venv but lives at `~/.local/bin/ruff` — scripts pointing to `.venv/bin/ruff` will fail; use system ruff
- All 5 merchants succeeded on first attempt — no retries needed

## Verification

- 84 pytest tests: all passed
- ruff: All checks passed
- AC-1 ✅: crawl_run rows exist for merchants 3-7
- AC-2 ✅: products grew from 38 → 597

## Follow-Ups

- **SC-75**: Crawl batch 2, merchants 8-11 (Blue Bottle, Stumptown, Heart, George Howell)
- **SC-76**: Crawl batch 3, merchants 12-15
- **SC-61/62/63**: Metadata parsing — products still have sparse origin/process/roast-level fields
- Consider noting ruff path discrepancy in AGENTS.md or pyproject.toml dev-dependencies
