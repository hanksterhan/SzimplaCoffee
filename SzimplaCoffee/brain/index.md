# SzimplaCoffee Brain

The second brain supports **continuity, not narrative**. It exists so any agent (or human) picking up this project can understand what happened, what was decided, and what's next — without re-reading every commit.

## Structure

```
brain/
├── index.md                    # You are here
├── backlog/
│   └── now-next-later.md       # Prioritized work queue
├── decisions/
│   └── NNN-<title>.md          # Architecture Decision Records (ADRs)
├── research/
│   └── <topic>.md              # Deep dives, analysis, spike results
├── merchant-intel/
│   └── <merchant-slug>.md      # Per-merchant notes, quirks, API findings
└── worklog/
    └── YYYY-MM-DD-<slug>.md    # What was done in each work session
```

## Active Artifacts

- `north-star.md` — Product vision and principles (read-only reference)
- `comprehensive-plan.md` — Architecture and execution plan (read-only reference)
- `CLAUDE.md` — Agent instructions for any AI working on this repo
- `brain/backlog/now-next-later.md` — Current priorities
- `brain/worklog/` — Session-by-session implementation log

## Rules

1. **Architecture changes require a decision record.** Create `decisions/NNN-<title>.md` with context, options considered, decision, and consequences.
2. **High-value merchants get an intel file.** One file per merchant in `merchant-intel/` with API quirks, crawl notes, quality observations.
3. **Every work session updates the worklog.** What was done, what broke, what was learned.
4. **Backlog stays current.** After each session, update `now-next-later.md` to reflect reality.
5. **Research is durable or deleted.** Long analysis gets converted into a decision record or removed. No stale research.
6. **Don't duplicate north-star or comprehensive-plan.** Reference them, don't copy them into brain files.

## Decision Record Template

```markdown
# NNN — Title

**Date:** YYYY-MM-DD
**Status:** accepted | superseded | deprecated

## Context
What prompted this decision?

## Options Considered
1. Option A — pros/cons
2. Option B — pros/cons

## Decision
What we chose and why.

## Consequences
What changes as a result. What we gain, what we lose.
```
