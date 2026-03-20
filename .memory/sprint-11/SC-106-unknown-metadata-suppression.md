# SC-106 — Unknown metadata suppression in catalog UX

## What changed

- Extracted catalog metadata display helpers into `frontend/src/lib/product-tags.ts`.
- Centralized `normalizedOrNull()` so canonical metadata values of `"unknown"` are treated as absent.
- Centralized `buildTags()` so product tags prefer canonical fields and never emit `"unknown"`.
- Updated `frontend/src/routes/products.lazy.tsx` to import the shared helpers.
- Added `"quality"` to the `ProductSort` union in `frontend/src/hooks/use-products.ts` so the existing sort option is type-safe.
- Added frontend unit coverage with Vitest in `frontend/src/lib/__tests__/product-tags.test.ts` and `frontend/vitest.config.ts`.

## Why it changed

The catalog UX should not expose internal sentinel values like `unknown` as if they were meaningful user-facing metadata. The product page already leaned on normalized metadata; this ticket made the suppression explicit, testable, and reusable.

## Verification

- `cd frontend && npm test -- --reporter=dot` → 13 tests passed
- `cd frontend && npm run build` → passed
- `cd frontend && npx tsc -b` → passed
- `cd backend && . .venv/bin/activate && pytest tests/ -q` → 298 passed

## Notes

- The current products page does not yet render a roast/process facet picker, so the practical UX win in this ticket is tag/display suppression plus test coverage.
- Adding Vitest is a small but useful infrastructure improvement for future frontend-only tickets.
