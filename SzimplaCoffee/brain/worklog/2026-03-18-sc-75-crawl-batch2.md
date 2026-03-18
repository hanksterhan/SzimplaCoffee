# 2026-03-18 - SC-75 crawl batch 2

Completed SC-75 closeout work:

- verified scheduler-created `crawl_runs` rows for merchants 8-12
- confirmed batch 2 raised total products from 597 after SC-58 to 890
- documented merchant-level results for Blue Bottle, Stumptown, Heart, George Howell, and Passenger
- recorded Blue Bottle as a completed generic crawl with 0 records written / 0 products so the gap is visible without treating the ticket as failed
- closed the ticket, wrote delivery memory, and updated autopilot state

Verification completed:

- `cd backend && .venv/bin/pytest tests/ -q`
- `cd backend && ~/.local/bin/ruff check src/ tests/`
