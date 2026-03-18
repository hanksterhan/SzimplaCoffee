# SC-75 Delivery Memory — Crawl Batch 2 (Blue Bottle, Stumptown, Heart, George Howell, Passenger)

**Date:** 2026-03-18  
**Ticket:** SC-75  
**Sprint:** 02

## What Changed

Verified that the scheduled crawl batch for merchants 8-12 completed successfully at **2026-03-18 08:02 UTC** and closed out the ticket.

| Merchant | Adapter | Records Written | DB Products | Crawl Quality | Notes |
|---|---|---:|---:|---:|---|
| Blue Bottle Coffee (8) | generic | 0 | 0 | 0.244 | Completed run, but generic adapter did not ingest product data |
| Stumptown Coffee (9) | shopify | 80 | 35 | 0.917 | Successful crawl |
| Heart Coffee Roasters (10) | shopify | 19 | 5 | 0.917 | Successful crawl |
| George Howell Coffee (11) | shopify | 246 | 48 | 0.917 | Successful crawl |
| Passenger (12) | shopify | 949 | 154 | 0.917 | Successful crawl |

- **Products after SC-58:** 597
- **Products after batch 2 verification:** 890
- **Net growth vs SC-58 baseline:** +293 products
- **Crawl runs present for all merchants 8-12:** yes

## Why

SC-75 was the second merchant-coverage batch in Sprint 2. The underlying crawl work had already been performed by the scheduler, so this autopilot cycle focused on verifying the persisted evidence, documenting the Blue Bottle gap, and formally closing the ticket.

## Surprises / Notes

- Blue Bottle did not hard-fail; it recorded a `completed` crawl run through the generic adapter, but wrote **0** records and left the merchant with **0** products. This is a merchant-specific crawl quality gap, not a ticket failure.
- The strongest ingestion in this batch was Passenger with **154** products in the database and **949** records written during crawl.
- SC-76 is now fully unblocked as the final crawl batch.
- `ruff` still lives at `~/.local/bin/ruff`, not in `.venv/bin/`.

## Verification

- `cd backend && .venv/bin/pytest tests/ -q` → **123 passed**
- `cd backend && ~/.local/bin/ruff check src/ tests/` → **All checks passed**
- AC-1 ✅: `crawl_runs` rows exist for merchants 8-12 and all show `completed`
- AC-2 ✅: products increased from **597** after SC-58 to **890** after batch 2 verification

## Follow-Ups

- **SC-76**: Crawl batch 3 for merchants 13-15 and verify ingestion
- **SC-60**: Review and promote crawled merchants based on crawl quality
- Consider a future ticket for Blue Bottle custom-platform handling if it remains strategically important
