# SC-97 Execution Plan — Improve metadata fill rate: expand parser patterns

## Goal

Expand `coffee_parser.py` normalization patterns for `roast_level` and `process_family`
to reduce the current ~30% roast-unknown and ~50% process-unknown rates in the active
catalog. All new patterns must be test-covered. Run backfill to verify real-world impact.

## Context

- `backend/src/szimplacoffee/services/coffee_parser.py` contains `_normalize_roast_level`
  and `_normalize_process_family` functions with regex/keyword matching.
- Products with `roast_level='unknown'` (277/918) and `process_family='unknown'` (458/918)
  can potentially be resolved by expanding these pattern sets.
- `szimpla backfill-metadata` re-runs the parser over all active products and updates
  canonical fields. It already works end-to-end.
- No schema migrations needed — fields already exist.

## Files Expected to Change

- `backend/src/szimplacoffee/services/coffee_parser.py` — pattern expansion
- `backend/tests/test_coffee_parser.py` — new test cases for added patterns

## Implementation Steps

### S1 — Expand roast_level patterns

1. Open `coffee_parser.py` and read `_normalize_roast_level`.
2. Sample unknowns from the DB to identify unmatched terms:
   ```sql
   SELECT name, roast_cues FROM products WHERE roast_level='unknown' AND is_active=1 LIMIT 50;
   ```
3. Add patterns for terms not yet matched, e.g.:
   - "blonde" → "light"
   - "nordic", "scandinavian" → "light"
   - "city", "city+" → "medium" / "medium-dark"
   - "full city" → "medium-dark"
   - "french", "italian" → "dark"
   - "extra dark", "double roast" → "dark"
   - "half-caff" → do not assign roast (skip or use context)
   - Common degree codes or numeric-roast references if present
4. Write test cases in `test_coffee_parser.py` using the `parse_coffee_metadata` entry point.

### S2 — Expand process_family patterns

1. Read `_normalize_process_family` in `coffee_parser.py`.
2. Sample unknowns from DB:
   ```sql
   SELECT name, process_text FROM products WHERE process_family='unknown' AND is_active=1 LIMIT 50;
   ```
3. Add patterns for terms not yet matched, e.g.:
   - "giling basah", "wet-hulled", "wet hulled" → "washed" (closest analog) or new "wet-hulled" enum value
   - "semi-washed", "semi washed", "pulped natural" → "natural" or dedicated enum
   - "double fermented", "extended fermentation" → "washed" or "anaerobic"
   - "anaerobic natural" → "natural"
   - "anaerobic washed" → "washed"
   - "carbonic maceration" → "natural" (or "experimental" if enum supports it)
   - "lactic" → "washed"
   - "experimental" — if product has no other process signal, skip (do not over-classify)
4. Write test cases.

### S3 — Run backfill and report

1. Ensure the app is not running a crawl concurrently.
2. Record baseline counts:
   ```sql
   SELECT roast_level, COUNT(*) FROM products GROUP BY roast_level;
   SELECT process_family, COUNT(*) FROM products GROUP BY process_family;
   ```
3. Run: `cd backend && . .venv/bin/activate && szimpla backfill-metadata`
4. Re-run count queries and record improvement.
5. Note before/after in delivery memory.

## Risks / Notes

- Do not over-classify: if a term is ambiguous, leave as "unknown" rather than guess.
- `process_family` enum values in use: check what values the codebase actually accepts
  (likely: "washed", "natural", "honey", "unknown"). Adding new enum values may affect
  frontend filters — check if process_family values are enumerated anywhere in the frontend.
- Keep changes minimal and test-first. A failing test is better than a wrong classification.

## Verification

```bash
cd backend && .venv/bin/pytest tests/test_coffee_parser.py -v
cd backend && .venv/bin/pytest tests/ -q
```

Check fill rate improvement via:
```bash
cd backend && . .venv/bin/activate && szimpla backfill-metadata
# then query: SELECT roast_level, COUNT(*) FROM products WHERE is_active=1 GROUP BY roast_level;
```

## Out of Scope

- Storing description_html for richer context
- ML/LLM classification
- Farm-name → origin mapping
- Parser architecture refactors
