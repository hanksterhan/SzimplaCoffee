# SC-6 — Merchant Filtering and Sorting in Dashboard and Discovery Queue — Execution Plan

## Summary

Add filter and sort controls to the merchant list and discovery queue pages. Filters (crawl_tier, trust_tier, platform_type, is_active) and sort options (name, last_crawl_at, quality score) are driven by URL query parameters, enabling bookmarkable filtered views. HTMX handles partial refresh on filter change.

---

## Slices

### S1 — Add filter/sort query parameter handling to merchant list route

**Goal:** The `/merchants` route accepts and applies filter/sort query params, returning correctly filtered SQLAlchemy results.

**Files to create:**
- `tests/test_merchant_list_filter_sort.py`

**Files to modify:**
- `src/szimplacoffee/main.py`

**Implementation notes:**

1. Update the merchant list route to accept optional query params:
   ```
   GET /merchants?tier=A&trust=high&platform=shopify&active=true&sort=name&order=asc
   ```

2. Build dynamic query:
   ```python
   q = session.query(Merchant)
   if tier: q = q.filter(Merchant.crawl_tier == tier)
   if trust: q = q.filter(Merchant.trust_tier == trust)
   if platform: q = q.filter(Merchant.platform_type == platform)
   if active is not None: q = q.filter(Merchant.is_active == active)

   sort_map = {
       "name": Merchant.name,
       "last_crawl_at": ...,  # join with crawl_runs subquery
       "quality": MerchantQualityProfile.overall_quality_score,
   }
   q = q.order_by(sort_map.get(sort, Merchant.name))
   ```

3. For `last_crawl_at` sort: use a correlated subquery or lateral join to get the most recent `finished_at` per merchant from `crawl_runs`.

4. Pass active filter values back to template context so the UI can reflect them in form state.

5. Tests:
   - Filter by `tier=A` returns only tier A merchants
   - Filter by `platform=shopify` returns only Shopify merchants
   - Sort by `name` returns alphabetical order
   - Filter params are reflected in response URL/context (bookmarkable)

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_merchant_list_filter_sort.py -v
```

---

### S2 — Update merchant list template with filter/sort controls

**Goal:** The merchant list UI has a functional filter/sort bar that uses HTMX to refresh the table without full page reload.

**Files to modify:**
- `src/szimplacoffee/templates/merchant_list.html`

**Implementation notes:**

1. Add a filter bar above the merchant table:
   ```html
   <form hx-get="/merchants" hx-target="#merchant-table" hx-trigger="change">
     <select name="tier">
       <option value="">All tiers</option>
       <option value="A" {% if filters.tier == 'A' %}selected{% endif %}>Tier A</option>
       ...
     </select>
     <select name="sort">
       <option value="name">Name</option>
       <option value="last_crawl_at">Last crawl</option>
       <option value="quality">Quality score</option>
     </select>
   </form>
   ```

2. Wrap the merchant table in a div with `id="merchant-table"` so HTMX can target it.

3. For HTMX partial responses, add a route variant or a `HX-Request` header check in the main route to return table-only HTML when requested via HTMX.

4. URL param reflection: the filter form `<select>` values should reflect the current filter state from the template context (passed from route).

**Checks:**
- Manual: change filter dropdown → table updates without full page reload
- Inspect URL after filter change → query params are present

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
```

Manual verification:
1. Navigate to `/merchants` — filter bar is visible
2. Select "Tier A" from crawl tier filter — only tier A merchants appear
3. Select "Quality score" sort — merchants sorted by quality
4. Copy URL with filters — paste in new tab → same filtered view loads

---

## Notes

- Keep filter form simple. Avoid JavaScript beyond HTMX attributes.
- Operator tool first — prefer functional over polished.
- If `last_crawl_at` sort is complex to implement with the current DB query, sort by `updated_at` as a reasonable proxy for v1 and add a follow-up ticket.
- Discovery queue (`/discovery`) should get the same filter treatment in a follow-up — out of scope here to keep the ticket focused.
