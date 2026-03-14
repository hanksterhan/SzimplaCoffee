# SC-5 — Richer Product-Note Parsing — Execution Plan

## Summary

Build a `product_note_parser.py` module that uses regex and keyword heuristics to extract structured origin, process, variety, roast cues, and tasting notes from raw product descriptions. Wire it into the crawl pipeline so new products get enriched fields. Set `is_espresso_recommended` based on parsed signals.

---

## Slices

### S1 — Build product note parser

**Goal:** A standalone, well-tested parser module with extraction for all target fields.

**Files to create:**
- `src/szimplacoffee/services/product_note_parser.py`
- `tests/test_product_note_parser.py`
- `tests/fixtures/product_descriptions.py`

**Implementation notes:**

#### `product_note_parser.py` — `parse_product_notes(description: str) -> ParsedProductNotes`

Return type:
```python
@dataclass
class ParsedProductNotes:
    origin_text: str | None
    process_text: str | None
    variety_text: str | None
    roast_cues: str | None
    tasting_notes_text: str | None
    is_espresso_recommended: bool
    confidence: float
```

**Origin extraction:**
- Known countries: Ethiopia, Kenya, Colombia, Guatemala, Honduras, Peru, Brazil, Yemen, Burundi, Rwanda, El Salvador, Costa Rica, Panama, Bolivia, Mexico, Indonesia, Sumatra, PNG
- Known regions: Yirgacheffe, Sidama, Huila, Antioquia, Antigua, Gedeo, Guji
- Pattern: match against word boundary, case-insensitive

**Process extraction:**
- Keywords: `washed`, `natural`, `honey`, `anaerobic`, `wet process`, `dry process`, `semi-washed`, `pulped natural`, `carbonic maceration`
- Normalize to canonical: `washed | natural | honey | anaerobic | other`

**Variety extraction:**
- Keywords: `typica`, `bourbon`, `caturra`, `catuai`, `geisha`, `gesha`, `SL28`, `SL34`, `heirloom`, `74110`, `74112`, `pacamara`, `maragogipe`

**Roast cues:**
- Light: `light roast`, `light-roast`, `lightly roasted`, `filter roast`, `nordic`
- Medium: `medium roast`, `medium-roast`, `balanced`, `all-purpose`
- Dark: `dark roast`, `espresso roast`, `bold`, `italian`, `french`

**Tasting notes:**
- Pattern after trigger phrases: `notes of`, `tasting notes:`, `flavors of`, `cup notes`, `we taste`
- Extract comma-separated phrases up to sentence boundary
- Normalize to lowercase

**Confidence:** 1.0 if 3+ fields parsed, 0.7 if 2 fields, 0.4 if 1 field, 0.0 if none.

**Test fixtures** (in `tests/fixtures/product_descriptions.py`):
```python
FIXTURES = [
    {
        "description": "Ethiopia Yirgacheffe Natural. Notes of blueberry, jasmine, and dark chocolate. Light roast.",
        "expected_origin": "Ethiopia",
        "expected_process": "natural",
        "expected_roast_cues": "light",
        "expected_tasting_notes_contains": ["blueberry", "jasmine"],
    },
    # Add 4 more real-world-ish examples
]
```

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_product_note_parser.py -v
```

---

### S2 — Wire parser into crawl pipeline and set espresso_recommended flag

**Goal:** New products extracted during crawl get enriched origin/process/tasting fields and espresso flag set.

**Files to modify:**
- `src/szimplacoffee/services/crawlers.py`

**Implementation notes:**

1. After extracting raw product data, call `parse_product_notes(description)`.
2. Map parsed fields to product model:
   - `origin_text = parsed.origin_text or existing`
   - `process_text = parsed.process_text or existing`
   - `variety_text = parsed.variety_text or existing`
   - `roast_cues = parsed.roast_cues or existing`
   - `tasting_notes_text = parsed.tasting_notes_text or existing`
3. Set `is_espresso_recommended`:
   - True if: roast_cues in (light, medium) AND no dark roast signal AND no "not for espresso" text
   - True if: "espresso" or "espresso-forward" appears in description positively

4. Add tests to `test_product_note_parser.py` covering:
   - Product with "Ethiopia Natural Light Roast" → `is_espresso_recommended = True`
   - Product with "French Roast Dark" → `is_espresso_recommended = False`
   - Fields are stored in correct model columns

**Checks:**
```bash
ruff check src/ tests/
pytest tests/ -v -k "test_product_note_parser"
```

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
```

Manual check:
1. Run a crawl on a known merchant
2. Query products table — confirm `origin_text`, `process_text`, `tasting_notes_text` are populated
3. Check `is_espresso_recommended` is set correctly for a known espresso-appropriate coffee

---

## Notes

- Parser should be pure (no DB calls). Takes a string, returns a dataclass.
- Don't overwrite existing fields if confidence is lower than what's already stored (future: confidence-gated updates).
- Tasting notes normalization: lowercase, strip trailing punctuation, de-duplicate.
- This is intentionally regex/heuristic-only for v1. LLM enrichment is explicitly out of scope.
