# SC-43 Execution Plan

## Goal

Polish the `/products` catalog so it is faster to browse and compare coffee: multi-select categories, smarter coffee filtering for mis-tagged bean products, better whole-bean cards, and an inline detail dialog.

## Context

The current catalog uses a single category select and card click navigates away to a separate route. Some coffee items appear to be stored as `merch`, which makes the default coffee view miss legitimate beans.

## Files / Areas Expected to Change

- `backend/src/szimplacoffee/api/products.py`
- `backend/tests/test_api_products.py`
- `frontend/src/hooks/use-products.ts`
- `frontend/src/routes/products.lazy.tsx`

## Implementation Steps

1. Add backend parsing for multi-category filters.
2. Add helper logic so the coffee filter includes coffee-like whole-bean products even when their stored category is `merch`.
3. Add backend tests covering multi-category filtering and the coffee fallback behavior.
4. Update the frontend products hook to send multiple categories.
5. Replace the single category `<select>` with multi-select toggle chips/buttons.
6. Refine product cards so whole-bean cards emphasize merchant, price, and bag size.
7. Open a dialog on card click and load richer product detail there.
8. Show the best available metadata in the dialog: link, tags, weight, variants, and description/fallback copy.

## Risks / Notes

- There is no dedicated long-description field in the current product schema, so the dialog should degrade gracefully when detailed copy is unavailable.
- Coffee-like heuristics should be conservative enough not to pull obvious apparel into the coffee filter.
- Keep route-level structure intact; this should be a catalog UX improvement, not a broader navigation rewrite.

## Verification

- Run focused backend tests for product API filtering.
- Run frontend lint/type checks if practical.
- Manual verification on `/products` for:
  - multi-select category behavior
  - known mis-tagged coffee visibility
  - whole-bean card summary fields
  - product detail dialog behavior

## Out of Scope

- Schema migration for a first-class product description field
- Rewriting crawler classification across the entire ingestion pipeline
- Replacing the standalone `/products/$productId` route
