# SC-37 Execution Plan: Products Page with Search

## Overview
Full catalog browser with search, filtering, and sorting across all merchants.

## Execution
1. **API:** Extend GET /api/v1/products with query params: search, merchant_id, origin, process, min_price, max_price, in_stock, sort_by, offset, limit
2. **Backend:** SQLite LIKE queries for search, WHERE clauses for filters, ORDER BY for sorting, LIMIT/OFFSET for pagination
3. **Page:** Route /products — search bar + filter sidebar + product card grid
4. **Search:** Debounced text input searching name, origin_text, process_text, tasting_notes_text
5. **Filters:** Merchant multi-select, origin dropdown (populated from distinct values), process dropdown, price range
6. **Cards:** Product name, merchant, origin tag, process tag, price, availability badge
