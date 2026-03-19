# SC-95 Execution Plan

## Goal

Improve crawl trust by adding per-merchant quality/reliability signals and by enforcing low-CPU serialized or staggered crawl execution behavior.

## Context

Phase 2 prioritizes crawl quality over raw merchant expansion. The user also explicitly required that no session/CPU be overloaded during execution.

## Files / Areas Expected to Change

| File | Change |
|------|--------|
| `backend/src/szimplacoffee/services/scheduler.py` | Constrain execution shape |
| `backend/src/szimplacoffee/services/*crawl*` | Improve quality signal capture |
| `backend/src/szimplacoffee/models.py` | Persist new quality fields if needed |
| `backend/tests/*` | Add/adjust crawl quality and scheduling tests |

## Implementation Steps

1. Inspect current crawl scheduling and execution fan-out behavior.
2. Identify the minimal quality signals needed for merchant trust decisions (e.g. recent success rate, parse completeness, availability quality, product-count stability).
3. Persist or compute those signals in the current architecture.
4. Adjust routine crawl execution to prefer serialized or staggered work and avoid multiple heavy jobs at once.
5. Add regression coverage for the new behavior.
6. Verify bounded crawl execution and test results.

## Risks / Notes

- Avoid turning this into a broad scheduler rewrite.
- Prefer deterministic, observable quality signals over speculative scoring.
- Preserve forward progress while keeping machine load conservative.

## Verification

- Targeted crawl/scheduler tests
- Full backend tests if shared contracts change
- Bounded execution proof that heavy crawl work is not parallelized routinely

## Out of Scope

- Top-500 merchant expansion
- Full crawl-monitoring UI redesign
- Historical deal baseline work
