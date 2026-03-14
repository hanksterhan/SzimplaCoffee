# 001 — Second Brain System Design

**Date:** 2026-03-14
**Status:** accepted

## Context

SzimplaCoffee is developed by a human-agent team. Agents wake up fresh each session with no memory of prior work. The project needs a durable knowledge system that:

- Survives agent resets
- Is version-controlled alongside code
- Is readable by both humans and agents
- Captures decisions, not just logs

## Options Considered

1. **External tools (Notion, wiki)** — Good for humans, bad for agents. Requires API integration. Not version-controlled with code.
2. **Single MEMORY.md file** — Simple but grows unwieldy. No structure for different knowledge types.
3. **Structured markdown brain in repo** — Version-controlled, diffable, structured by purpose. Easy for agents to read and write.

## Decision

Use a repo-local structured markdown system under `SzimplaCoffee/brain/` with distinct directories for decisions, research, merchant intel, worklog, and backlog.

Agent instructions live in `CLAUDE.md` at repo root. Vision docs (`north-star.md`, `comprehensive-plan.md`) are read-only references, not duplicated into the brain.

## Consequences

- Every agent session starts by reading `CLAUDE.md` → `brain/index.md` → `brain/backlog/now-next-later.md`
- Work gets logged immediately, not retroactively
- Architecture decisions are traceable with full context
- Merchant-specific knowledge accumulates across sessions
- The brain is part of the git history — rollbacks, diffs, and blame all work
