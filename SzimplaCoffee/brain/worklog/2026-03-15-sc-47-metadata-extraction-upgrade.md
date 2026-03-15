# 2026-03-15 - SC-47 metadata extraction upgrade

Completed SC-47 delivery work:

- extended the coffee parser to emit normalized origin, process family, roast level, confidence, and provenance
- fixed the crawler classifier contradiction so filter-roast coffees are not rejected up front
- added merchant regex patterns and product-level metadata override tables for explicit corrections
- wired crawler enrichment and product upsert paths to persist normalized metadata and override provenance
- expanded backend parser tests to cover normalized fields, override behavior, and the filter classifier regression

Verification completed:

- `cd backend && ../.venv/bin/pytest tests/test_coffee_parser.py -q`
- `cd backend && ../.venv/bin/ruff check src/szimplacoffee/services/coffee_parser.py src/szimplacoffee/services/crawlers.py src/szimplacoffee/models.py tests/test_coffee_parser.py`
- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- draft PR opened at `https://github.com/hanksterhan/SzimplaCoffee/pull/4`
