# SC-1 — Crawl-Health and Merchant-Error Visibility — Execution Plan

## Summary

Add crawl health observability to the SzimplaCoffee web UI. The merchant detail page will show the latest crawl run status, error summary, and stale-data badge. A new crawl health dashboard page will list recent runs across all merchants. All logic is driven by the existing `crawl_runs` table.

---

## Slices

### S1 — Add crawl health query helpers and stale-data logic

**Goal:** Create a service module that queries `crawl_runs` and computes stale-data state per merchant.

**Files to create:**
- `src/szimplacoffee/services/crawl_health.py`
- `tests/test_crawl_health.py`

**Files to modify:**
- `src/szimplacoffee/db.py` (if session helpers need updating)

**Implementation notes:**

1. In `crawl_health.py`, implement:
   - `get_latest_crawl_run(session, merchant_id) -> CrawlRun | None`
   - `get_recent_crawl_runs(session, limit=50) -> list[CrawlRun]`
   - `is_merchant_stale(merchant, latest_run) -> bool` — uses crawl_tier to determine threshold:
     - Tier A: stale after 6 hours
     - Tier B: stale after 24 hours
     - Tier C: stale after 7 days
     - Tier D: never considered stale (on-demand)
   - `get_crawl_health_summary(session) -> list[dict]` — merchant + latest run + stale flag

2. Write tests covering:
   - Stale threshold logic for each tier
   - Query returns most recent run per merchant (not just any run)
   - Graceful handling of merchants with no crawl runs

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_crawl_health.py -v
```

---

### S2 — Wire crawl health into merchant detail and health dashboard templates

**Goal:** Surface crawl health data in the web UI on the merchant detail page and a new crawl health dashboard page.

**Files to create:**
- `src/szimplacoffee/templates/crawl_health.html`

**Files to modify:**
- `src/szimplacoffee/main.py` (add `/crawl-health` route, update merchant detail route)
- `src/szimplacoffee/templates/merchant_detail.html` (add crawl status section)

**Implementation notes:**

1. Add `/crawl-health` route to `main.py`:
   - Calls `get_crawl_health_summary()`
   - Renders `crawl_health.html` with merchant+run data

2. Update merchant detail route to include latest crawl run and stale flag via `get_latest_crawl_run()` and `is_merchant_stale()`.

3. `crawl_health.html` template:
   - Table: merchant name | last crawl | status | adapter | records | error summary | stale badge
   - Color-code status: success=green, error=red, running=blue
   - Stale badge: orange warning when stale

4. `merchant_detail.html` additions:
   - New "Crawl Status" section showing last run status, adapter, records written, error summary
   - Stale-data badge if `is_stale=True`

5. Write tests for:
   - `/crawl-health` route returns 200
   - Stale badge present when last crawl exceeds tier threshold
   - Merchant detail page includes crawl status section

**Checks:**
```bash
ruff check src/ tests/
pytest tests/ -v -k "test_merchant_detail_crawl_health or test_crawl_health_page or test_stale_data_badge"
```

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
```

Manually verify:
1. Visit `/crawl-health` — confirm table renders with merchant crawl data
2. Visit a merchant detail page — confirm crawl status section is present
3. Manually set a merchant's last crawl to > 6h ago (tier A) — confirm stale badge appears

---

## Notes

- Keep template logic minimal. All staleness computation belongs in `crawl_health.py`, not Jinja.
- If HTMX partial refresh is desired for the crawl health page, it's a nice-to-have, not required for AC pass.
- Error summary should truncate to 200 chars in the UI to avoid layout breakage.
