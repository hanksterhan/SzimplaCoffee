# SC-63 Execution Plan

## Goal
Improve coffee_parser.py process and roast level extraction patterns. Achieve >70% fill rate on real product descriptions.

## Context
Process (washed/natural/honey) and roast level (light/medium/dark) are first-class recommendation dimensions. Both fields are nearly empty. Target: >70% fill rate based on typical description coverage.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/coffee_parser.py`
- `backend/tests/test_coffee_parser.py`

## Implementation Steps
1. Collect 20+ real descriptions from DB (see SC-62 for query)
2. Read current process/roast patterns in coffee_parser.py
3. Add/extend process patterns:
   - washed: "washed", "wet process", "fully washed"
   - natural: "natural", "dry process", "naturally processed", "sun-dried"
   - honey: "honey", "honey process", "pulped natural", "semi-washed"
   - anaerobic: "anaerobic", "anaerobic natural", "anaerobic washed"
   - carbonic: "carbonic maceration"
4. Add/extend roast level patterns:
   - light: "light roast", "light", "lightly roasted", "filter roast", "pour over roast"
   - medium: "medium roast", "medium", "all-rounder"
   - medium-dark: "medium-dark", "medium dark"
   - dark: "dark roast", "dark", "bold", "full city"
   - espresso: "espresso roast", "espresso blend" → medium-dark
5. Handle ambiguity: if multiple roast levels match, pick most specific
6. Add pytest tests: at least 5 per category (10 per field = 20+ tests)
7. Run backfill and measure fill rate

## Risks / Notes
- "Light" alone can false-positive on "light body" — require "light roast" or word boundary context
- Process often appears in tasting notes section, not always the title

## Verification
```bash
cd backend && pytest tests/test_coffee_parser.py -v -k "process or roast"
cd backend && python -c "
from szimplacoffee.db import engine
from sqlalchemy import text
conn = engine.connect()
total = conn.execute(text('SELECT COUNT(*) FROM products')).scalar()
for field in ['process', 'roast_level']:
    filled = conn.execute(text(f'SELECT COUNT(*) FROM products WHERE {field} IS NOT NULL')).scalar()
    print(f'{field}: {filled}/{total} = {filled/total*100:.1f}%')
"
```

## Out of Scope
- Origin patterns (SC-62)
- Variety/cultivar extraction
