# SC-87 Execution Plan

## Goal
Improve variety_text fill rate from 26% to ≥50% by expanding coffee_parser.py cultivar name patterns.

## Context
890 products. 234 (26%) have variety_text. Need 445+ (50%) to reach target. Specialty roasters commonly list cultivar names in product descriptions. Gesha/Geisha is the most premium and most frequently listed. Bourbon, Caturra, Typica are extremely common across all growing regions.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/coffee_parser.py` — expand VARIETY_PATTERNS
- `backend/tests/test_coffee_parser.py` — add cultivar test cases

## Implementation Steps

1. **Audit current variety patterns**
   - Read `_extract_variety` or `VARIETY_PATTERNS` in coffee_parser.py
   - Sample 20 products with null variety_text: `SELECT name FROM products WHERE variety_text IS NULL LIMIT 20`

2. **Add patterns for common cultivars**
   Pattern list to add (case-insensitive):
   - Gesha / Geisha
   - Bourbon (Red Bourbon, Yellow Bourbon, Pink Bourbon)
   - Caturra
   - Catuai (Red Catuai, Yellow Catuai)
   - Typica
   - SL-28 / SL28 / SL 28
   - SL-34 / SL34
   - Pacamara
   - Pacas
   - Maragogipe / Maragogype
   - Wush Wush
   - Marsellesa
   - Heirloom (common for Ethiopian naturals)
   - Catimor
   - Mundo Novo
   - Castillo
   - Tabi
   - Ethiopia Landrace / Landrace
   - JAAS / Batian (Kenyan cultivars)

3. **Apply patterns**
   Match as case-insensitive substrings in product name and tasting_notes_text. Store matched canonical name in variety_text.

4. **Run backfill**
   ```bash
   cd backend && szimpla backfill-metadata
   ```

5. **Verify fill rate**
   ```bash
   cd backend && .venv/bin/python -c "
   import sys; sys.path.insert(0,'src')
   from szimplacoffee.db import engine
   from sqlalchemy import text
   c = engine.connect()
   t = c.execute(text('SELECT COUNT(*) FROM products')).scalar()
   f = c.execute(text(\"SELECT COUNT(*) FROM products WHERE variety_text IS NOT NULL AND variety_text != ''\")).scalar()
   print(f'{f}/{t} = {round(100*f/max(t,1))}%')
   "
   ```

6. **Add tests**
   - Parametrized test: `@pytest.mark.parametrize("text,expected", [("Gesha lot 12", "Gesha"), ("natural Bourbon", "Bourbon"), ...])`

## Risks / Notes
- "Bourbon" matches too broadly if product names include "Bourbon Street" or whiskey-aged coffees — use word boundaries
- "Heirloom" is used loosely by many roasters; match it but note it's low-specificity
- SC-85 should run first (blocker) to establish backfill pipeline confidence

## Verification
```bash
cd backend && .venv/bin/pytest tests/ -q
```
Target: ≥50% variety fill rate after backfill

## Out of Scope
- Origin improvements (SC-85)
- Frontend changes
