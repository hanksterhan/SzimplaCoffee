# SC-102 Execution Plan — Improve Metadata Fill Rate for Roast, Process, and Origin

## Goal

Reduce the fraction of active products with `unknown` roast_level / process_family and
missing origin_country by improving coffee parser patterns and adding a lightweight
non-coffee product classifier. Target: roast ≤ 20%, process ≤ 35% after re-run.

Before counts (2026-03-20):
- roast_level unknown: 283/919 (30%)
- process_family unknown: 451/919 (49%)
- origin_country null/blank: 343/919 (37%)

## Context

- `SC-94` added canonical normalized fields with confidence + provenance to all products.
- `szimpla backfill-metadata` is the CLI command that re-runs the coffee parser over all
  existing products using their stored `name` field (not description, which is not stored).
- Parser lives in `backend/src/szimplacoffee/services/` — likely `parser.py`.
- Unknown values inflate filter dropdowns with a meaningless "unknown" option, weakening
  catalog trust and recommendation ranking.
- Non-coffee products (grinders, subscriptions, gift cards, syrups) artificially inflate
  the unknown count — they shouldn't count against fill rate targets.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/services/parser.py` (or equivalent parser module)
  - New roast_level patterns
  - New process_family patterns
  - Lightweight non-coffee keyword classifier

## Implementation Steps

### S1 — Audit

1. Read `services/parser.py` to understand current pattern structure.
2. Run a query to find top 30 product names with unknown roast and unknown process:
   ```sql
   SELECT name, roast_level, process_family, origin_country
   FROM products WHERE is_active=1 AND roast_level='unknown'
   ORDER BY name LIMIT 30;
   ```
3. Categorize findings: how many are gear/non-coffee vs. coffee with missed patterns?

### S2 — Parser Improvements

Add to existing patterns (do not restructure):

**Roast patterns** (missed terms to add):
- `blonde` → light
- `city+` / `city plus` → medium
- `full city` / `full city+` → medium-dark
- `northern italian` → dark
- `scandinavian` → light
- `omni roast` → medium (omni-roast is designed for multiple brew methods)
- `espresso roast` → medium-dark
- `nordic` → light

**Process patterns** (missed terms to add):
- `carbonic maceration` / `cm process` → washed (special)
- `extended fermentation` → fermented
- `anaerobic natural` → natural (anaerobic)
- `honey washed` / `honey-washed` → honey
- `lactic` / `lactic fermentation` → fermented
- `thermal shock` → special process
- `double fermentation` → fermented

**Non-coffee classifier**:
Add a keyword-based check before parsing: if the product name matches known non-coffee
tokens, set a flag or skip normalization:
```python
NON_COFFEE_TOKENS = [
    "grinder", "tamper", "portafilter", "basket", "knock box", "dripper",
    "gooseneck", "kettle", "scale", "subscription box", "gift card",
    "merchandise", "mug", "syrup", "sauce", "spice", "chocolate",
    "brewing equipment", "accessories"
]
```
If matched → set `is_coffee_product = False` in parser result; backfill CLI should
set `metadata_confidence = 0.0` or skip normalization fields for these.

### S3 — Backfill and Verify

1. Run `szimpla backfill-metadata` (from backend venv).
2. Count after:
   ```sql
   SELECT
     COUNT(*) total,
     SUM(CASE WHEN roast_level='unknown' THEN 1 ELSE 0 END) roast_unknown,
     SUM(CASE WHEN process_family='unknown' THEN 1 ELSE 0 END) proc_unknown,
     SUM(CASE WHEN origin_country IS NULL OR origin_country='' THEN 1 ELSE 0 END) orig_null
   FROM products WHERE is_active=1;
   ```
3. Confirm roast ≤ 20% and process ≤ 35%.
4. If targets not met, do one more pass on the most common missed patterns.

## Risks / Notes

- Parser changes are additive (new patterns only) — minimal regression risk.
- Description field is not stored, so only product name parsing is available. This caps
  improvement potential; some coffees will remain unknown without richer crawl data.
- Non-coffee classifier should be conservative (keyword list only) to avoid false positives.
- `backfill-metadata` updates `roast_level`, `process_family`, `origin_country`,
  `metadata_confidence`, `metadata_provenance` in-place on Product rows.

## Verification

1. `cd backend && pytest tests/ -q` — must pass
2. `cd frontend && npm run build && npx tsc -b` — must pass
3. Before/after fill rate counts documented in delivery memory.

## Out of Scope

- Storing description_html (crawler changes, separate ticket)
- ML inference
- Frontend filter dropdown changes (separate ticket)
- Additional Product schema migrations unless strictly necessary
