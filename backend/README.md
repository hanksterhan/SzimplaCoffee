# Backend Notes

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
