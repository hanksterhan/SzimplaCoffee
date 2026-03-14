# SC-4 — Import Real Purchase History from Notion — Execution Plan

## Summary

Implement a working Notion import pipeline that reads from the user's Notion purchase history database, maps records to the `purchase_history` schema, de-duplicates on re-run, and exposes the flow via the `szimpla sync notion` CLI command.

---

## Slices

### S1 — Implement Notion API client and purchase history mapper

**Goal:** A `notion_import.py` service that connects to the Notion API and maps purchase history pages to `purchase_history` rows.

**Files to create:**
- `src/szimplacoffee/services/notion_import.py`
- `tests/test_notion_import.py`

**Files to modify:**
- `src/szimplacoffee/cli.py` (wire `szimpla sync notion` command)

**Implementation notes:**

1. **Dependencies:** Use `notion-client` SDK (already listed in pyproject.toml or add it).

2. **Configuration:** Read from environment or config:
   - `NOTION_API_KEY` — integration token
   - `NOTION_PURCHASE_HISTORY_DB_ID` — database ID for purchase history

3. **Notion property mapping** (adjust to actual Notion schema):
   | Notion Property | purchase_history field |
   |---|---|
   | Name (title) | `product_name` |
   | Merchant (select/relation) | `merchant_id` (lookup by name) |
   | Price (number) | `price_cents` (multiply by 100) |
   | Weight / Size (select or number) | `weight_grams` (parse or map) |
   | Date (date) | `purchased_at` |
   | Notion page ID | `source_ref` |

4. **Merchant lookup:** Match Notion merchant name to `merchants.name` (case-insensitive, fuzzy if needed). If no match, use `merchant_id = NULL` and log a warning.

5. **`source_system`:** Always `"notion"`.

6. **Test approach:** Mock the Notion API response with fixture data. Don't make live API calls in tests.

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_notion_import.py -v
```

---

### S2 — Add de-duplication and wire into CLI

**Goal:** Re-running `szimpla sync notion` is idempotent — no duplicate rows are created.

**Files to modify:**
- `src/szimplacoffee/services/notion_import.py`
- `src/szimplacoffee/cli.py`

**Implementation notes:**

1. **De-duplication key:** `(source_system='notion', source_ref=<notion_page_id>)`

2. **Strategy:** Before inserting, query for existing record with same `source_ref`. If found, skip (or update if price/date changed — decision: skip for v1).

3. **CLI integration:**
   ```python
   @app.command()
   def sync_notion():
       """Import purchase history from Notion."""
       ...
   ```
   Print summary: `Imported N records, skipped M duplicates, M warnings`.

4. **Test de-duplication:** Run import twice with same fixtures. Assert `purchase_history` count is the same after second run.

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_notion_import.py -v -k deduplication
```

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
```

Live verification (requires real Notion credentials):
```bash
szimpla sync notion
# Expect: "Imported N records, skipped M duplicates"
```

---

## Notes

- Don't fail hard on merchant lookup miss. Log warning, store with `merchant_id = NULL`, continue.
- Weight/size parsing: common values like "12oz", "340g", "1lb" should be normalized to grams. Add a `parse_weight_to_grams(text) -> int | None` helper.
- Notion API token should be read from env var, never hardcoded.
- For v1, skip updating existing records on re-import. Re-import is add-only.
