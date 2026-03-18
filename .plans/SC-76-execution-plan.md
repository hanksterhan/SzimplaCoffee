# SC-76 Execution Plan

## Goal
Crawl the final 3 merchants (La Colombe, Coava, Huckleberry) and produce a full crawl coverage summary for all 15 imported merchants.

## Context
Final batch of the 3-batch crawl split. After this ticket, SC-60 (trust promotion) and SC-61 (metadata audit) both unblock.

## Files / Areas Expected to Change
- `data/szimplacoffee.db` — crawl_runs and products rows added
- `.memory/` — coverage summary checkpoint

## Implementation Steps
1. Activate backend venv: `cd backend && source .venv/bin/activate`
2. Run crawl for merchants 13, 14, 15
3. Verify crawl_runs rows for merchants 13-15
4. Query overall coverage: `SELECT COUNT(DISTINCT merchant_id) FROM products` — target ≥8
5. Write coverage summary to `.memory/session-checkpoints/` including per-merchant status (success/fail/empty)

## Risks / Notes
- Coava (merchant 14) has a non-standard Shopify layout — may return empty products
- Huckleberry is standard WooCommerce — should work
- La Colombe has a more complex product catalog structure

## Verification
- `pytest tests/ -q`
- `ruff check src/ tests/`
- Coverage summary written to memory

## Out of Scope
- Fixing failed crawl adapters
- Metadata parsing
- Trust tier promotion
