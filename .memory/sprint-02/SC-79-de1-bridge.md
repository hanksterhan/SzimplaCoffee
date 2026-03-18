# SC-79: DE1 Visualizer Bridge

**Delivered:** 2026-03-18  
**Tests:** 7 new, 163 total (up from 156) — all passing  
**Ruff:** clean

## What Was Built

A polling bridge that auto-imports espresso shots from [visualizer.coffee](https://visualizer.coffee) as `BrewFeedback` records.

### Files Created
- `backend/alembic/versions/20260318_02_de1_bridge_state.py` — Migration adding `de1_bridge_state` table and new columns to `brew_feedback`
- `backend/src/szimplacoffee/services/de1_bridge.py` — Core bridge service (poll, parse, fuzzy-match, import)
- `backend/src/szimplacoffee/api/de1.py` — REST endpoints: GET `/api/v1/de1/status`, POST `/api/v1/de1/toggle`
- `backend/tests/test_de1_bridge.py` — 7 tests covering all ACs

### Files Modified
- `backend/src/szimplacoffee/models.py` — Added `De1BridgeState` model; updated `BrewFeedback` (nullable `purchase_id`, 7 new telemetry columns)
- `backend/src/szimplacoffee/config.py` — Added `VISUALIZER_USERNAME`, `VISUALIZER_API_KEY`, `DE1_AUTO_MATCH`, `DE1_DEFAULT_DOSE_GRAMS`
- `backend/src/szimplacoffee/api/__init__.py` — Registered `de1_router`
- `backend/src/szimplacoffee/main.py` — Added `_run_de1_bridge_job()` and APScheduler registration (every 5 min, conditioned on `VISUALIZER_USERNAME`)

## Key Decisions

1. **`purchase_id` made nullable** — DE1-imported shots have no purchase record. This is a schema change but safe: existing rows all have non-null values, and the `batch_alter_table` migration handles SQLite's lack of direct ALTER COLUMN.

2. **`bean_weight` not `grinder_dose_weight`** — The plan had the wrong field name. Verified against live API: the field is `bean_weight` (string, e.g. `"18.0"`).

3. **Scheduler in `main.py`** — The ticket plan mentioned `services/scheduler.py` but the actual codebase puts all APScheduler jobs in the `lifespan()` function in `main.py`. Followed existing pattern.

4. **`difflib.SequenceMatcher`** — No rapidfuzz in venv; stdlib difflib keeps dependency count flat.

5. **`De1BridgeState` is a singleton row** — Bridge state is fetched with `.limit(1)` and created if absent. Simpler than multi-user state tracking; sufficient for single-user deployment.

6. **Migration idempotency** — All migration steps check `_col_exists()` / `_table_exists()` before applying, making re-runs safe.

## What's Not Included (by design)

- UI for reviewing/approving matched shots (future ticket)
- Rating/notes auto-population (manual via existing form)
- Real Visualizer API calls in tests (all mocked with `unittest.mock.patch`)

## Sharp Edges

- `test_toggle_auto_match` shares the same `de1_bridge_state` table as other tests. The `clean_de1_data` autouse fixture truncates `de1_bridge_state` before/after each test.
- The fuzzy match threshold (75%) may produce no matches for short coffee names. This is acceptable — `product_id` stays null and the row is still created.
- Water temp uses `espresso_temperature_mix[0]` (first reading in the series), which is typically near the set point at brew start.
