# 2026-03-15 — SC-44 backend stability and package-root cleanup

Completed SC-44 delivery work:

- repaired the broken backend test module by pointing it at current recommendation-service helpers
- removed a pre-existing unused import that was blocking the backend lint gate
- moved the stray repository-root `src/` artifact path out of the repo
- added `/src/` to `.gitignore`
- documented `backend/src/szimplacoffee` as the canonical backend package root

Verification completed:

- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- package-root check shows only `./backend/src` and `./frontend/src`
