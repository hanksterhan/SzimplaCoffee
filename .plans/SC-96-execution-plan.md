# SC-96 Execution Plan

## Goal

Make catalog filtering/search/availability semantics trustworthy by tying them to normalized metadata and truthful backend semantics.

## Context

Phase 2 aims to improve data trust first. After SC-94 and SC-95, the next leverage point is making the catalog behave according to that trusted data rather than free-text or misleading presence semantics.

## Files / Areas Expected to Change

| File | Change |
|------|--------|
| `backend/src/szimplacoffee/api/*products*` | Tighten query semantics |
| `backend/src/szimplacoffee/services/*` | Use normalized metadata where needed |
| `frontend/src/routes/*products*` | Align UI semantics and placeholders |
| `frontend/src/components/*` | Correct stock/search messaging |
| `backend/tests/*` / `frontend` build | Regression coverage |

## Implementation Steps

1. Audit current product search, filtering, sorting, and stock semantics.
2. Tie backend filters/search to normalized metadata from SC-94.
3. Correct any misleading availability semantics.
4. Align frontend labels/placeholders with actual backend behavior.
5. Run backend tests and frontend build verification.

## Risks / Notes

- Keep this ticket focused on truth semantics, not broad UX redesign.
- Avoid coupling to future historical-deal work.
- Prefer additive backend parameters over breaking query-contract changes when possible.

## Verification

- Targeted backend/API checks for normalized filtering
- Backend tests
- Frontend build

## Out of Scope

- Historical deal intelligence
- Large catalog UX redesign
- Merchant expansion work
