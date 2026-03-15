# SC-30 Execution Plan: Coffee Metadata Parser

## Overview
Build a regex/heuristic parser that extracts structured coffee metadata from raw product descriptions (HTML).

## Pre-work
1. Sample 20+ product descriptions from the DB to understand real formats
2. Identify common patterns across Shopify and WooCommerce stores
3. Review what fields the Product model already has

## Execution

### S1: Core parser module (2-3 hours)
**Create:** `backend/src/szimplacoffee/services/metadata_parser.py`

**Approach:**
1. Define `CoffeeMetadata` dataclass: origin_country, origin_region, process_method, tasting_notes, roast_level, altitude, varietal, is_single_origin, is_espresso_suitable
2. Strip HTML → plain text using BeautifulSoup (reuse `_clean_text` from crawlers.py)
3. Origin extraction:
   - Regex for "Origin: X" / "Country: X" / "Region: X" patterns
   - Known country list matching (Ethiopia, Colombia, Kenya, Guatemala, etc.)
   - Region matching after country (Yirgacheffe, Huila, Nyeri, etc.)
4. Process extraction:
   - Regex for "Process: X" / "Processing: X"
   - Keyword scan: washed, natural, honey, anaerobic, wet-hulled, semi-washed
5. Tasting notes extraction:
   - Regex for "Tasting Notes: X" / "Notes: X" / "Flavor: X"
   - Look for comma-separated flavor descriptors
   - Common patterns: "notes of X, Y, and Z"

### S2: Extended parsing (1-2 hours)
- Roast level: light, medium, medium-dark, dark, omni
- Altitude: regex for MASL/masl patterns, "1800-2100m"
- Varietal: known varieties list (Gesha, Bourbon, Caturra, SL28, Typica, etc.)
- Single-origin vs blend: "blend" in name, multiple origins = blend
- Espresso suitability: "espresso" in name/description, "great for espresso", "espresso roast"

### S3: Tests (1-2 hours)
- Create `tests/fixtures/sample_descriptions.json` with 20+ real descriptions
- Test each extraction function independently
- Test full parse pipeline
- Test edge cases: empty strings, pure HTML, no coffee content

## Risks
- Description formats vary wildly between merchants — 80/20 rule applies
- Some descriptions are pure marketing with no structured data
- Regex won't catch everything — aim for high precision, accept lower recall

## Definition of Done
- Parser module importable and functional
- Tests pass with >80% accuracy on sample descriptions
- CoffeeMetadata dataclass covers all Product model metadata fields
