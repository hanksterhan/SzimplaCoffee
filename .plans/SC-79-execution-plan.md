# SC-79 Execution Plan — DE1 Visualizer Bridge

## Goal

Auto-import Decent Espresso DE1 shot data from visualizer.coffee into SzimplaCoffee's BrewFeedback table via a polling APScheduler job. Replace manual brew session logging with automatic ingestion, with fuzzy product matching and a runtime toggle.

## Constraints

- Ticket stays **draft** until `VISUALIZER_USERNAME` is provided
- No BLE / pyDE1 — Visualizer polling only
- Dose defaults to 18g when shot record omits it
- Auto-match defaults to on; user can toggle via API or config
- No new heavy dependencies — prefer stdlib `difflib` unless `rapidfuzz` is already present

## Files / Areas Expected to Change

| File | Change |
|------|--------|
| `backend/alembic/versions/20260318_02_de1_bridge_state.py` | New migration: `de1_bridge_state` table |
| `backend/src/szimplacoffee/config.py` | Add 4 config keys |
| `backend/src/szimplacoffee/models.py` | Add `De1BridgeState` ORM model |
| `backend/src/szimplacoffee/services/de1_bridge.py` | New service: poll, parse, match, upsert |
| `backend/src/szimplacoffee/scheduler.py` | Register de1_bridge job (every 5 min) |
| `backend/src/szimplacoffee/api/de1.py` | New router: GET /status, POST /toggle |
| `backend/src/szimplacoffee/main.py` | Mount de1 router |
| `backend/tests/test_de1_bridge.py` | New test file (7 test cases) |

## Implementation Steps

### S1 — DB foundation

1. Add to `config.py`:
   ```python
   VISUALIZER_USERNAME: str = ""
   VISUALIZER_API_KEY: str = ""         # optional, for private profiles
   DE1_AUTO_MATCH: bool = True
   DE1_DEFAULT_DOSE_GRAMS: int = 18
   ```

2. Add `De1BridgeState` model to `models.py`:
   ```python
   class De1BridgeState(Base):
       __tablename__ = "de1_bridge_state"
       id: Mapped[int] = mapped_column(primary_key=True)
       last_seen_shot_id: Mapped[Optional[str]]
       last_poll_at: Mapped[Optional[datetime]]
       shots_imported: Mapped[int] = mapped_column(default=0)
       auto_match: Mapped[bool] = mapped_column(default=True)
   ```

3. Write Alembic migration `20260318_02_de1_bridge_state.py` — creates the table. Run `alembic upgrade head`.

### S2 — Bridge service

`de1_bridge.py` structure:
```
poll_visualizer()          # fetch new shots from API
_parse_shot(raw)           # normalize shot JSON → internal dict
_fuzzy_match_product(db, brand, bean_type)  # returns product_id or None
_upsert_brew_feedback(db, shot_data)        # create BrewFeedback row
run_bridge(db)             # orchestrator called by scheduler
```

**Visualizer API call:**
```
GET https://visualizer.coffee/api/shots?username={VISUALIZER_USERNAME}
Authorization: Bearer {VISUALIZER_API_KEY}  # omit if public profile
```

Response is an array of shot objects. Walk newest-first, stop at `last_seen_shot_id`. After processing, update `de1_bridge_state.last_seen_shot_id` and `last_poll_at`.

**Shot field mapping:**
| Visualizer field | BrewFeedback field | Fallback |
|---|---|---|
| `grinder_dose_weight` | `dose_grams` | `DE1_DEFAULT_DOSE_GRAMS` (18) |
| `drink_weight` | `yield_grams` | null |
| `len(espresso_elapsed) * 0.1` | `brew_time_seconds` | null |
| `espresso_temperature_mix[0]` | `water_temp_c` | null |
| (always) | `machine` | `"DE1"` |
| fuzzy match | `product_id` | null if no match |

**Fuzzy matching:**
```python
from difflib import SequenceMatcher

def score(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

# Try: "{bean_brand} {bean_type}" against "{merchant.name} {product.name}"
# Accept if score >= 75
```

**Idempotency:** Each shot has a unique `id` from Visualizer. Store as `last_seen_shot_id`. On poll, skip any shot with id ≤ last_seen (or use a `de1_imported_shots` set if order isn't guaranteed).

### S3 — API endpoints

```python
# GET /api/v1/de1/status
{
  "enabled": true,
  "auto_match": true,
  "last_poll_at": "2026-03-18T08:45:00Z",
  "shots_imported": 12,
  "visualizer_username": "hank"
}

# POST /api/v1/de1/toggle
# Body: {"auto_match": false}
# Returns updated status
```

Mount router in `main.py`: `app.include_router(de1_router, prefix="/api/v1/de1")`

### S4 — Scheduler registration

In `scheduler.py`, alongside existing crawl jobs:
```python
scheduler.add_job(
    run_de1_bridge,
    trigger="interval",
    minutes=5,
    id="de1_bridge",
    replace_existing=True,
)
```

Only register if `settings.VISUALIZER_USERNAME` is non-empty (skip silently if not configured).

## Risks / Notes

- **Visualizer API shape** — the exact response schema should be verified against a real API call before writing the parser. The field names above are from Decent community docs but may differ slightly.
- **Private profile** — if the Visualizer profile is private, `VISUALIZER_API_KEY` is needed. Public profiles work with username only.
- **Shot deduplication** — if Visualizer doesn't guarantee ordering, use a separate `de1_imported_shot_ids` JSON column or a child table rather than a single `last_seen_shot_id`.
- **rapidfuzz** — check `pip show rapidfuzz` first. If present, use `fuzz.token_sort_ratio` (better for reordered strings like "Ethiopia Geometry" vs "Geometry Ethiopia").

## Verification

```bash
cd backend && pytest tests/test_de1_bridge.py -v   # 7 targeted tests
cd backend && pytest tests/ -q                     # full suite (AC-8)
cd backend && ~/.local/bin/ruff check src/ tests/
```

## Out of Scope

- BLE/pyDE1 direct connection
- Shot approval UI
- Rating auto-population
- Multi-user support
