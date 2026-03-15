# SC-44 Execution Plan

## Scope

Repair the backend regression suite and clean up package-root ambiguity so future work has a reliable quality gate.

## Out of Scope

- New product features
- Recommendation redesign
- Crawl architecture refactors beyond test enablement

## AC to Verification Mapping

- AC-1 → `cd backend && . .venv/bin/activate && pytest -q`
- AC-2 → `find . -maxdepth 2 -type d \( -name src -o -path './backend/src' \) | sort`
- AC-3 → `rg -n 'backend package root|canonical backend package root|one obvious backend package root' AGENTS.md CLAUDE.md README.md backend -S`

## Slice Boundaries

### S1 Repair broken backend test imports
- Files modify: `backend/tests/test_recommendations.py`, `backend/tests/`
- Files read only: `backend/src/szimplacoffee/main.py`, `backend/src/szimplacoffee/`
- Prohibited changes: do not reintroduce removed UI helpers just to satisfy old tests

### S2 Quarantine or remove stale top-level package artifacts
- Files modify: `src/`, `README.md`, `AGENTS.md`, `CLAUDE.md`
- Files read only: `backend/src/szimplacoffee/`
- Prohibited changes: do not break active entrypoints while cleaning the boundary

## Verification Commands

- `cd backend && . .venv/bin/activate && pytest -q`
- `cd backend && . .venv/bin/activate && ruff check src tests`
- `find . -maxdepth 2 -type d \( -name src -o -path './backend/src' \) | sort`
