# SC-62 — Coffee Parser Origin Expansion

**Delivered:** 2026-03-18T06:35:49Z  
**Status:** done

## What Changed

`backend/src/szimplacoffee/services/coffee_parser.py`:
- Added 24 new producing countries: Ecuador, Nicaragua, Tanzania, Uganda, China, Nepal, Vietnam, Myanmar, Laos, Thailand, India, Papua New Guinea, Malawi, Zambia, Zimbabwe, Cameroon, Congo, Madagascar, Cuba, Dominican Republic, Haiti, Jamaica.
- Added `_DEMONYMS` dict (23 entries): Ethiopian→Ethiopia, Colombian→Colombia, Kenyan→Kenya, Guatemalan→Guatemala, Honduran→Honduras, Peruvian→Peru, Brazilian→Brazil, Rwandan→Rwanda, Burundian→Burundi, Indonesian→Indonesia, Bolivian→Bolivia, Mexican→Mexico, Yemeni→Yemen, Ecuadorian→Ecuador, Nicaraguan→Nicaragua, Tanzanian→Tanzania, Ugandan→Uganda, Salvadoran→El Salvador, Panamanian→Panama, Indian→India, Nepali→Nepal, Vietnamese→Vietnam, Jamaican→Jamaica.
- Added `_HAWAII_VARIANTS` list: "Hawai'i", "Hawaiʻi", "Kona", "Maui", "Kauai" — all resolve to "Hawaii".
- Updated `_REGIONS` with 12 new regions: Harrar, Kirinyaga, Murang'a, Embu, Tarrazu, Tres Rios, Cajamarca, Puno, Minas Gerais, Cerrado, Mogiana, Aceh, Flores, Sulawesi, Kigali, Ngozi.
- `_extract_origin` now scans demonyms and Hawaii variants in addition to direct country names.
- `_normalize_origin_parts` resolves demonyms/Hawaii when no direct country match.
- `_count_countries` now deduplicates via set and includes demonym/Hawaii hits (prevents false blends).

`backend/tests/test_coffee_parser.py`:
- Added 14 new origin tests covering: Ecuador, China, Nepal, India, Nicaragua, Hawaii (diacritic), Kona, Ethiopian demonym, Colombian demonym, Kenyan demonym, Rwandan demonym, demonym-in-description-only, single-origin assertion, blend-via-demonyms.

## Results

- Origin fill rate: 64.8% → **66.8%** (+15 newly parsed, 399/597 products)
- Test suite: 84 → **98 tests passing**
- ruff: clean

## Surprises

- Most products at 64.8% were already matched by the existing country list — the gain from new countries was +2% delta (mainly Ecuador/India/China/Nepal products).
- Many remaining "no origin" products are genuinely non-coffee (merchandise, subscriptions, equipment) or opaque blend names. Those won't improve without descriptions.
- SC-61 confirmed descriptions are not stored in the DB — `description_text` column doesn't exist. Product names are the only parsing surface until SC-63 handles in-name clues or a description migration happens.

## Follow-Ups

- SC-63 (process/roast) can reuse the same pattern — add more roast demonyms and region keywords.
- A future ticket should store `description_text` from crawl payloads to unlock description-based parsing.
- Consider adding `_COUNTRIES` lookup for "Decaf" tag patterns (Goodnight Moon Decaf, Smiley Decaf) to avoid false country matches.
