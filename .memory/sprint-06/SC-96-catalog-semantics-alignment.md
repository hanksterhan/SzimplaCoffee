# SC-96 — Catalog Semantics Alignment Delivery Memory
_Delivered: 2026-03-19T21:45:00Z_

## What Changed

**Backend:**
- Added `has_stock: bool = False` field to `ProductSummary` (and inherited by `ProductDetail`).
- In `_build_product_result`, after computing `has_stock` from variant-level truth, it is now assigned to `summary.has_stock` so it propagates through the API response.
- In the single-product `get_product` endpoint, `has_stock` is computed post-validation from the variant objects (same logic: `is_available + latest_offer.is_available`).

**Frontend:**
- `schema.d.ts`: Added `has_stock: boolean` to both `ProductDetail` and `ProductSummary` schemas.
- `products.lazy.tsx`:
  - `ProductCard`: availability badge now uses `product.has_stock` (variant truth) instead of `product.is_active` (presence flag).
  - `ProductQuickView` header row: availability display uses `product.has_stock`.
  - `ProductQuickView` metadata grid: origin/process/roast now prefer canonical `origin_country`/`process_family`/`roast_level` with `origin_text`/`process_text`/`roast_cues` as fallback. Values of "unknown" are treated as null/absent.
  - `buildTags()`: same normalized-first, suppress-unknown logic applied to the badge tag list.
  - Added `normalizedOrNull()` utility to suppress "unknown" from display.

## Surprises / Notes

- Backend scope was smaller than the ticket originally estimated — backend filter queries were already using normalized fields correctly. The main work was frontend display alignment.
- TypeScript requires explicit parentheses around `??` and `||` when mixed (`||` and `??` cannot be mixed without parens in strict mode).
- The `has_stock` field is now also surfaced on the single-product API, not just catalog search. This makes both the card list and the quick-view dialog consistent.
- `ProductDetail` inherits `has_stock` from `ProductSummary` cleanly since it's a Pydantic subclass.

## What Phase 2 Looks Like Now

- ✅ SC-93: Autopilot startup noise eliminated
- ✅ SC-94: Canonical metadata normalization (origin_country, roast_level, process_family with confidence/provenance)
- ✅ SC-95: Crawl quality observable, serialized execution
- ✅ SC-96: Catalog display aligned to normalized metadata and variant-level stock truth

Phase 2 core is done. The next run should trigger backlog refill (0 ready tickets < min_ready_tasks=2).

## Follow-Ups

- Backlog refill needed: no open tickets remain. Next run should create tickets from Phase 3 candidates in brainstorm-current.md (SC-97 through SC-103 candidates).
- "unknown" fill rate (30% roast, 50% process) is still a concern but is a Phase 3 concern — SC-97 candidate exists for parser improvement.
- Consider declaring Phase 2 goal complete after the next brainstorm confirms criteria are satisfied.
