# .plans/ — Execution Plans

Every ticket in `.tickets/open/` has a corresponding execution plan here.

## Naming Convention

```
.plans/SC-{N}-execution-plan.md
```

The plan file is referenced from the ticket's `context_refs` field.

## What Goes in an Execution Plan

An execution plan is a detailed, agent-readable breakdown of exactly how to implement the ticket. It complements the ticket (which defines *what* and *why*) with the *how*.

### Recommended Structure

```markdown
# SC-N — Ticket Title — Execution Plan

## Summary
One-paragraph summary of the approach.

## Slices

### S1 — Slice Title
**Goal:** What this slice achieves.

**Files to create:**
- `src/szimplacoffee/...`

**Files to modify:**
- `src/szimplacoffee/...`

**Implementation notes:**
Step-by-step guidance for the implementer.

**Checks:**
- `ruff check src/ tests/`
- `pytest tests/ -v`

## Verification Steps
Full list of commands to run before marking the ticket `done`.

## Notes
Any caveats, edge cases, or future considerations.
```

## Rules

1. **One plan per ticket.** Plans are not shared between tickets.
2. **Plans are living documents.** Update them as implementation reveals complexity.
3. **Plans do not replace tickets.** The ticket is the source of truth for status and acceptance. The plan is implementation detail.
4. **Archive, don't delete.** When a ticket closes, its plan stays in `.plans/` for reference.
