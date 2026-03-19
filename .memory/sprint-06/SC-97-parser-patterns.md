# SC-97 — Parser Pattern Expansion + CLI Circular Import Fix

**Delivered:** 2026-03-19T23:42 Pacific  
**Branch:** feat/SC-97-parser-patterns → merged to stage

## What Changed

### coffee_parser.py
- `_normalize_roast_level`: added blonde, nordic/scandinavian variants, city/city+ terms,
  full city (medium-dark), extra dark, cinnamon roast, light-medium bridge terms (filter+espresso),
  medium dark (spaced), and broadened "light" to catch bare "light" as a word
- `_normalize_process_family`: added giling basah/wet-hulled, semi-washed/semiwashed,
  honey color variants (white/red/black/yellow), double fermented, extended fermentation,
  lactic, co-ferment, carbonic maceration, experimental → anaerobic

### test_coffee_parser.py
- 21 new parametrized test cases (11 roast, 10 process) added in SC-97 section
- All 271 tests pass

### db.py + bootstrap.py — Circular Import Fix
- **Bug**: `szimpla backfill-metadata` CLI was broken by a circular import:
  `cli.py → bootstrap.py → db.py → ensure_schema → bootstrap._apply_lightweight_migrations`
  (bootstrap not yet fully initialized)
- **Fix**: moved `_apply_lightweight_migrations` into `db.py` (no model dependencies, just
  SQLAlchemy `inspect` + `text`). Removed duplicate in `bootstrap.py`; bootstrap now imports
  it from `db.py`. The URL normalization block that was inside the migration was split into
  a separate `_normalize_merchant_urls()` called from `init_db()`.

## Backfill Results

| Field | Before | After | Delta |
|-------|--------|-------|-------|
| roast unknown | 277 | 276 | -1 |
| process unknown | 457 | 455 | -2 |

**Why so small?** The remaining ~276 roast and ~455 process unknowns have empty
`roast_cues` / `process_text` fields — they're non-coffee merchandise, subscriptions, gifts,
and single-origin coffees with no process descriptor in the product name. Name-only parsing
is at its practical ceiling. Storing `description_html` or re-crawling with richer extraction
is the next lever (separate ticket scope).

## Follow-ups
- SC-98 (deal baselines in catalog API) is next most impactful
- Description-storing ticket would unlock the next round of fill-rate gains
