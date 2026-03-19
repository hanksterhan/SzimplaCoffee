# SC-85 Execution Plan

## Goal
Improve origin_country fill rate from 61% to ≥70% by adding demonym → country mappings and alternate spellings to coffee_parser.py, then running backfill-metadata.

## Context
890 products exist. 545 (61%) have origin_country set. Need 623+ (70%) to satisfy the goal criterion. Gap is ~78 more products. The parser likely misses "Ethiopian", "Colombian", "Kenyan" etc. (demonym forms) and abbreviations like "PNG" for Papua New Guinea.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/coffee_parser.py` — add DEMONYM_MAP and apply in origin extraction
- `backend/tests/test_coffee_parser.py` — add test cases for new demonym patterns

## Implementation Steps

1. **Audit coffee_parser.py**
   - Find `_extract_origin` or `ORIGIN_PATTERNS` — understand current matching logic
   - Sample 10-20 products with null origin_country to see what text they have (query: `SELECT name, origin_text FROM products WHERE origin_country IS NULL LIMIT 20`)

2. **Add DEMONYM_MAP**
   Add a dict mapping demonym → ISO country name. At minimum:
   - Ethiopian → Ethiopia
   - Colombian → Colombia
   - Kenyan → Kenya
   - Guatemalan → Guatemala
   - Honduran → Honduras
   - Peruvian → Peru
   - Rwandan → Rwanda
   - Burundian → Burundi
   - Yemeni → Yemen
   - PNG / Papua → Papua New Guinea
   - Tanzanian → Tanzania
   - Ugandan → Uganda
   - Mexican → Mexico
   - Brazilian → Brazil
   - Bolivian → Bolivia
   - Indonesian → Indonesia
   - Panamanian → Panama

3. **Apply DEMONYM_MAP in extraction**
   After regex matching, check if the extracted text is a known demonym and map to canonical country name.

4. **Add alternate spelling patterns**
   - Sumatra → Indonesia (regional, common coffee origin)
   - Java → Indonesia
   - Sulawesi → Indonesia
   - Sidama / Sidamo → Ethiopia
   - Yirgacheffe / Yirga Cheffe → Ethiopia
   - Huila / Nariño / Tolima → Colombia (regional → country)
   - Antigua → Guatemala

5. **Run backfill**
   ```bash
   cd backend && .venv/bin/python -c "from szimplacoffee.cli import app; app()" backfill-metadata
   ```
   Or: `cd backend && .venv/bin/szimpla backfill-metadata`

6. **Verify fill rate**
   ```bash
   cd backend && .venv/bin/python -c "
   import sys; sys.path.insert(0,'src')
   from szimplacoffee.db import engine
   from sqlalchemy import text
   c = engine.connect()
   t = c.execute(text('SELECT COUNT(*) FROM products')).scalar()
   f = c.execute(text(\"SELECT COUNT(*) FROM products WHERE origin_country IS NOT NULL AND origin_country != ''\")).scalar()
   print(f'{f}/{t} = {round(100*f/max(t,1))}%')
   "
   ```

7. **Add/update tests**
   - `test_coffee_parser.py`: add parametrized test for each demonym → country mapping
   - Ensure existing tests still pass

## Risks / Notes
- Regional names like Sidama, Yirgacheffe map to Ethiopia but should not overwrite a more specific `origin_region` if already set
- Do not overwrite `origin_country` if it already has a value — only fill nulls
- backfill-metadata re-runs the parser over all products but only updates null fields (verify this behavior first)

## Verification
```bash
cd backend && .venv/bin/pytest tests/ -q
cd backend && .venv/bin/python -c "..." # fill rate query above
```
Target: ≥70% (≥623/890)

## Out of Scope
- Variety or process improvements (SC-87)
- Frontend changes
- New crawl runs
