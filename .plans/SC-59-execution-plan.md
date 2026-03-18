# SC-59 Execution Plan

## Goal
Add a `szimpla import-merchants --file merchants.txt` CLI command that reads a newline-delimited URL list, imports each merchant, and reports per-URL success/failure.

## Context
Manual one-at-a-time import via `szimpla add-merchant` is slow. A bulk import command enables efficient seed list ingestion. The command should reuse existing add-merchant logic rather than reimplementing it.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/cli.py` (new `import-merchants` command)
- `backend/src/szimplacoffee/bootstrap.py` (may extract add_merchant helper if not already standalone)

## Implementation Steps
1. Inspect current `cli.py` to understand existing `add-merchant` command structure
2. Extract or confirm a standalone `add_merchant(url)` helper function
3. Add `import-merchants` Click command with `--file` option:
   ```python
   @cli.command()
   @click.option("--file", "filepath", required=True, type=click.Path(exists=True))
   def import_merchants(filepath):
       """Import merchants from a newline-delimited URL file."""
       ...
   ```
4. Read file, skip blank lines and `#` comments, iterate URLs
5. Per URL: call `add_merchant()`, catch exceptions, track success/failure counts
6. Print summary: `Imported: 12, Skipped (duplicate): 3, Failed: 2`
7. Test with a real file including valid URLs, duplicates, and an invalid URL

## Risks / Notes
- File encoding: assume UTF-8
- URLs may include trailing whitespace — strip before use
- Existing `add-merchant` may have side effects (crawl trigger) — verify and disable if needed for bulk import

## Verification
```bash
# Test with valid URLs
echo "https://bluebottlecoffee.com" > /tmp/test_merchants.txt
cd backend && . .venv/bin/activate && szimpla import-merchants --file /tmp/test_merchants.txt

# Test duplicate skip
szimpla import-merchants --file /tmp/test_merchants.txt 2>&1 | grep -i skip

# Test invalid URL
echo "not-a-url" > /tmp/bad.txt
szimpla import-merchants --file /tmp/bad.txt 2>&1 | grep -i fail
```

## Out of Scope
- Async or parallel import
- GUI import interface
- Crawling after import
