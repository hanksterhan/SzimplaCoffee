# SC-105 Execution Plan

## Goal

Expand the merchant catalog by importing the next 10 verified merchants from the seed list using serialized, low-CPU CLI operations.

## Context

SC-101 increased active merchants from 16 to 26. The next safe growth step is another small serialized import batch.

## Files / Areas Expected to Change

- No source files required
- DB state via CLI operations
- Delivery memory and checkpoint files

## Implementation Steps

1. Read seed list and exclude already imported domains.
2. Prefer Shopify/WooCommerce, espresso-relevant US roasters.
3. Verify URLs before import.
4. Run `szimpla add-merchant <url> --crawl-now` one at a time.
5. Run `szimpla score-merchants` and summarize results.

## Risks / Notes

- Avoid custom-platform merchants when possible.
- Use `--crawl-now`; plain `add-merchant` is a known foot-gun.
- Keep the run serialized to respect CPU guardrails.

## Verification

- `cd backend && . .venv/bin/activate && szimpla score-merchants`
- `cd backend && pytest tests/ -q`

## Out of Scope

- Adapter or crawler code changes
- Bulk parallel import
- Manual platform-specific fixes
