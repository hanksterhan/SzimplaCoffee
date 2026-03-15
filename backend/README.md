# Backend Notes

## Recurring crawl scheduling (SC-50)

### How the scheduler works

The backend uses [APScheduler](https://apscheduler.readthedocs.io/) to run a recurring crawl loop while the FastAPI server is running.

- **Job frequency**: every 15 minutes (configurable).
- **Per-merchant cadence**: each execution inspects *which* merchants are actually due based on their crawl tier before doing any network work.
- **Tier thresholds** (defined in `services/scheduler.py`):
  | Tier | Interval |
  |------|----------|
  | A    | 6 hours  |
  | B    | 24 hours |
  | C    | 7 days   |
  | D    | manual only (never auto-scheduled) |
- A merchant with no crawl history is always considered due.
- Only `completed` crawl runs reset the freshness clock. A `failed` run does not.

### Observing scheduler state

The `/api/v1/crawl/schedule` endpoint returns current freshness status for every active merchant:

```bash
curl http://localhost:8000/api/v1/crawl/schedule | python3 -m json.tool
```

Status values: `fresh`, `approaching`, `overdue`, `never_crawled`, `manual`.

Trigger an immediate scheduled crawl (all due merchants):

```bash
curl -X POST http://localhost:8000/api/v1/crawl/run-due
```

### How much history before daily-sales data is trustworthy

- **Meaningful trends**: ≥7 days of consecutive crawls for Tier A/B merchants
- **Sale detection (compare-at-price)**: available from the first crawl that captures a `compare_at_price`
- **Pattern-based sale detection**: requires ≥14 days of offer history per variant

Do not claim daily-deal accuracy before sufficient history has accrued. The scheduler accumulates this automatically once started.

## Normalized product metadata

SC-46 introduces canonical product metadata fields alongside the existing free-text columns on `products`:

- `origin_country`
- `origin_region`
- `roast_level`
- `process_family`
- `metadata_confidence`
- `metadata_source`

The free-text fields remain the audit and display source of truth. The normalized fields exist so later tickets can add trustworthy filtering, sorting, and deal facts without reparsing every request.

## Migration path

Run the schema migration from the backend directory:

```bash
cd backend
.venv/bin/alembic upgrade head
```

This applies the first Alembic revision against the existing SQLite database and adds the normalized metadata columns plus indexes for the planned product filters.

The app still keeps a lightweight startup compatibility shim in `szimplacoffee.bootstrap` so an older local database can start safely before Alembic is adopted everywhere. Alembic is the canonical path for reproducible schema changes going forward.

## Backfill path

After the migration, run the metadata backfill script to populate the new normalized fields from current product names and free-text metadata:

```bash
cd backend
PYTHONPATH=src uv run python scripts/backfill_product_metadata.py
```

What the backfill currently does:

- fills missing free-text metadata from the parser when possible
- derives `origin_country` and `origin_region` from `origin_text`
- derives `process_family` from parsed or existing process text
- derives `roast_level` from parsed or existing roast cues
- records parser confidence in `metadata_confidence`
- marks parser-derived rows with `metadata_source=parser`

This is an incremental path, not a claim of full-corpus perfection. Higher-confidence merchant-specific overrides and richer field extraction remain follow-on work.
