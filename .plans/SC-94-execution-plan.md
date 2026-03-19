# SC-94 Execution Plan

## Goal

Introduce canonical metadata normalization fields and confidence/provenance semantics so SzimplaCoffee can treat origin, roast, and process as trustworthy product attributes rather than loose free-text hints.

## Context

The app already has improving parser output, but current filtering/search trust is limited by free-text-heavy storage. Phase 2 is explicitly focused on metadata normalization quality and trust.

## Files / Areas Expected to Change

| File | Change |
|------|--------|
| `backend/src/szimplacoffee/models.py` | Add or extend normalized metadata storage |
| `backend/src/szimplacoffee/services/coffee_parser.py` | Emit canonical values + confidence/provenance |
| `backend/src/szimplacoffee/services/*` | Update backfill/post-crawl wiring as needed |
| `backend/src/szimplacoffee/schemas/*` | Expose normalized metadata where appropriate |
| `backend/tests/*` | Add regression coverage |

## Implementation Steps

1. Inspect current product metadata fields and parser outputs.
2. Add canonical metadata support for:
   - `origin_country`
   - `roast_level`
   - `process_family`
   - confidence/provenance metadata
3. Wire parser/backfill flow to populate canonical values for active coffee products.
4. Keep raw text fields for audit/display; do not remove useful existing metadata.
5. Add targeted tests for canonical normalization and confidence/provenance semantics.
6. Run full backend tests.

## Risks / Notes

- Avoid a broad schema redesign beyond what Phase 2 needs.
- Prefer additive changes that preserve current app behavior.
- Keep provenance explicit so later UI/ranking work can distinguish structured truth from low-confidence guesses.

## Verification

- Targeted tests for normalized metadata behavior
- Full backend test suite
- Representative parser/backfill verification on existing products

## Out of Scope

- Historical deal scoring
- Full metadata review UI
- Merchant-specific override tooling beyond minimal foundations
