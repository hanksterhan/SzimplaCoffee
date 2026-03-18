# SC-62 Execution Plan

## Goal
Improve coffee_parser.py origin extraction patterns to achieve >50% fill rate on real product data.

## Context
Origin extraction is critical for recommendations. Most specialty coffee product descriptions explicitly name the origin country but current patterns miss many variants (demonyms, region names, abbreviations).

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/coffee_parser.py`
- `backend/tests/test_coffee_parser.py`

## Implementation Steps
1. Pull 20-50 real product descriptions from DB:
   ```bash
   cd backend && python -c "
   from szimplacoffee.db import engine
   from sqlalchemy import text
   rows = engine.connect().execute(text('SELECT name, description FROM products WHERE description IS NOT NULL LIMIT 50')).fetchall()
   for r in rows: print('---', r[0], r[1][:200] if r[1] else '')
   "
   ```
2. Read current origin patterns in coffee_parser.py
3. Identify misses in the sample descriptions
4. Add/extend origin patterns to cover:
   - Country names: Ethiopia, Colombia, Kenya, Guatemala, Rwanda, Brazil, Peru, Honduras, Costa Rica, El Salvador, Indonesia, Yemen, Burundi
   - Demonyms: Ethiopian, Colombian, Kenyan, Guatemalan, Rwandan, Brazilian, etc.
   - Region names: Yirgacheffe, Huila, Nyanza, Antigua (map to country)
5. Add pytest tests using real description snippets
6. Run backfill-metadata and measure fill rate improvement

## Risks / Notes
- Avoid over-matching: "Colombian dark roast blend" should extract Colombia but not misfire on "combination"
- Region-to-country mapping requires a lookup dict — keep it in coffee_parser.py constants
- Case-insensitive matching required

## Verification
```bash
cd backend && pytest tests/test_coffee_parser.py -v -k origin
cd backend && . .venv/bin/activate && szimpla backfill-metadata 2>&1
cd backend && python -c "
from szimplacoffee.db import engine
from sqlalchemy import text
total = engine.connect().execute(text('SELECT COUNT(*) FROM products')).scalar()
filled = engine.connect().execute(text('SELECT COUNT(*) FROM products WHERE origin IS NOT NULL')).scalar()
print(f'origin: {filled}/{total} = {filled/total*100:.1f}%')
"
```

## Out of Scope
- Process and roast level patterns (SC-63)
- Variety/cultivar extraction
