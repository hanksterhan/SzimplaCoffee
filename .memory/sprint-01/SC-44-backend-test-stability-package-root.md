# SC-44 — Backend test stability and package root cleanup

## What changed

- Updated `backend/tests/test_recommendations.py` to assert against the current recommendation-service helper surface instead of removed display helpers from `szimplacoffee.main`.
- Removed an unrelated unused import in `backend/src/szimplacoffee/api/products.py` so the backend lint gate could pass again.
- Quarantined the stray repository-root `src/` artifact path by moving the local directory out of the repo and adding `/src/` to `.gitignore`.
- Documented `backend/src/szimplacoffee` as the canonical backend package root in `README.md`, `AGENTS.md`, and `CLAUDE.md`.

## Why it changed

The backend regression suite was failing during test collection because one test module still targeted helpers that no longer exist. At the same time, the repository still had a stale top-level `src/` artifact path that made the package boundary look ambiguous. Fixing both reestablishes the backend test and lint gate as a reliable prerequisite for the next ticket batch.

## Notes / sharp edges

- Backend verification currently depends on the root repo venv, not `backend/.venv`, because `backend/.venv` does not contain `pytest` or `ruff`.
- The stray top-level `src/` path was a local artifact, not a tracked repo directory. The permanent repo-side protection is the new `/src/` ignore rule plus the explicit docs.

## Verification

- `cd backend && ../.venv/bin/pytest -q`
- `cd backend && ../.venv/bin/ruff check src tests`
- `find . -maxdepth 2 -type d \( -name src -o -path './backend/src' \) | sort`
