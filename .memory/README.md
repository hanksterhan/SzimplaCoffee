# .memory/ — Delivery Memory

This directory holds structured memory for the SzimplaCoffee agentic engineering process. It tracks what was learned, decided, and discovered during delivery — beyond what git history captures.

## Purpose

- **Continuity across sessions:** Agents wake up fresh. Memory files prevent re-learning the same things.
- **Delivery context:** What worked, what failed, what was tried during a specific ticket.
- **Sprint-level summaries:** Periodic synthesis of what happened across a sprint.

## Structure

```
.memory/
├── README.md          # This file
├── index.json         # Searchable index of all memory entries
└── sprint-01/         # Sprint-scoped memory files
    └── ...
```

## Memory Entry Format

Each memory file is a markdown file. Naming convention:

```
sprint-01/SC-N-<short-slug>.md
```

### Recommended Structure

```markdown
# SC-N — What Was Learned

**Date:** YYYY-MM-DD
**Ticket:** SC-N
**Phase:** implementation | debugging | verification

## What happened
Brief description.

## What was learned
Key insight, pattern, or decision.

## What to remember next time
Distilled guidance for future agents or sessions.
```

## index.json

The index tracks all memory entries for quick lookup:

```json
{
  "entries": [
    {
      "id": "sprint-01/SC-1-crawler-notes",
      "ticket": "SC-1",
      "date": "2026-03-14",
      "summary": "Short one-line summary"
    }
  ]
}
```

## Rules

1. **Write it down during the session, not after.** Fresh observations are more accurate.
2. **Be specific.** Vague notes like "things were complicated" have no value.
3. **Update index.json** when adding a new memory file.
4. **Sprint folders are permanent.** Do not delete or archive them — they are the delivery record.
