# SC-110 Execution Plan: Description-Based Metadata Backfill Re-Pass

## Goal

Re-run the coffee metadata parser over all active products that have `description_text != NULL`
but still have weak/missing `origin_country`, `roast_level`, or `process_family`.
Improve origin coverage from ~56% toward 70%+.

## Context

SC-104 stored `description_text` for all products during crawl. The subsequent `backfill-metadata`
command ran before descriptions were widely populated. Re-running it now — constrained to products
with description_text — should extract origin signals from richer source text.

The metadata parser lives in `backend/src/szimplacoffee/services/` and is invoked by the
`backfill-metadata` CLI command. We'll add a `backfill-descriptions` command (or extend
`backfill-metadata` with a `--descriptions-only` flag) that re-runs the parser selectively.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/cli.py` — add new CLI command
- `backend/src/szimplacoffee/services/parser.py` (or equivalent metadata service) — add/expose re-pass function
- `backend/tests/test_backfill_descriptions.py` — new test file

## Implementation Steps

1. **Inspect existing backfill command** in `cli.py` and the parser service to understand
   how metadata extraction works and what fields/confidence values are updated.

2. **Add `backfill-descriptions` CLI command** that:
   - Queries `Product` where `is_active=True` AND `description_text IS NOT NULL`
   - For each product, runs the metadata extractor against `description_text` (possibly combined with `name`)
   - Only updates `origin_country`, `roast_level`, `process_family` where new confidence > existing confidence
   - Prints before/after counts: `origin_country: 500/891 → 620/891`

3. **Write backend test** in `tests/test_backfill_descriptions.py`:
   - Create test products with description_text containing clear origin signals
   - Run the re-pass function
   - Assert metadata fields are populated

4. **Run verification**: `pytest tests/ -q` and `ruff check src/ tests/`

## Risks / Notes

- The fill rate gain may be less than expected if descriptions are terse. Accept 60%+ as meaningful.
- Do not force-fill with low-confidence guesses — only update when confidence improves.
- The parser may already handle description_text; check the existing implementation first.
- If `backfill-metadata` already supports descriptions, the change may be minimal (just a flag or filter).

## Verification

```bash
cd backend && . .venv/bin/activate
szimpla backfill-descriptions   # Should print before/after counts
pytest tests/ -q
~/.local/bin/ruff check src/ tests/
```

Also manually check the fill rate:
```python
from szimplacoffee.db import get_session
from szimplacoffee.models import Product
s = next(get_session())
total = s.query(Product).filter(Product.is_active==True).count()
filled = s.query(Product).filter(Product.is_active==True, Product.origin_country!=None).count()
print(f"{filled}/{total} = {filled/total*100:.1f}%")
```

## Out of Scope

- No new crawl runs
- No parser rule changes
- No frontend changes
- No schema changes
