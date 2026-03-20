# SC-106 Execution Plan

## Goal

Suppress "unknown" metadata values from all visible catalog filter UX and product tag display without changing backend data or query logic.

## Context

SC-94 and SC-102 added canonical normalized fields (roast_level, process_family, origin_country) to all active products. A meaningful fraction remain "unknown" (roast ~20%, process ~35%), which now appear in the frontend filter panel as selectable options and as visible chips in product cards. This is confusing — "unknown" is not a meaningful user-facing filter choice. The fix is entirely in the frontend display layer.

## Files / Areas Expected to Change

- `frontend/src/routes/products.lazy.tsx` — filter panel option rendering
- `frontend/src/components/ProductCard.tsx` — tag display / buildTags logic
- Possibly `frontend/src/hooks/useProducts.ts` if facets come from there
- New: `frontend/src/components/__tests__/buildTags.test.ts` (unit test)

## Implementation Steps

1. **Audit filter option source**: Determine where roast/process filter options are generated (hardcoded array vs. derived from API facets). Add `.filter(v => v && v !== 'unknown')` to option list generation.
2. **Audit buildTags / ProductCard**: Find where roast_level, process_family, origin_country are converted to visible chips/tags. Add guard: if value is null, undefined, or 'unknown', skip tag.
3. **Audit product metadata display**: Any place that shows "Unknown origin" or "Unknown roast" as text — convert to empty/absent rendering.
4. **Extract buildTags if inline**: If the tag-building logic is inline in a component, extract to a pure utility function so it can be unit tested.
5. **Write unit test**: `buildTags({roast_level:'unknown', process_family:'unknown', origin_country: null})` returns no tags with those values.
6. **Build verification**: `npm run build && npx tsc -b`

## Risks / Notes

- No backend changes needed: this is entirely display-layer suppression.
- The DB retains "unknown" values — they are useful for internal data quality tracking.
- After SC-105 adds 10 new merchants, some new products may have unknown metadata; this ticket ensures the UX stays clean regardless.
- Check `frontend/src/hooks/` for any facet or filter-option hooks that might need updating.

## Verification

1. `cd frontend && npm run build`
2. `cd frontend && npx tsc -b`
3. `cd backend && pytest tests/ -q` (regression: backend unaffected)
4. Manual check: open /products catalog, confirm no "unknown" in filter panel or product tags

## Out of Scope

- No DB value changes
- No backend endpoint or schema changes
- No recommendation scoring changes
- No WooCommerce or Shopify adapter changes
