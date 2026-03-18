# SC-70: recommendation_run_id linkage to PurchaseHistory

**Delivered:** 2026-03-18
**Status:** Done
**Branch:** main (b774bb1)

## What Changed

- `models.py`: Added `recommendation_run_id: Mapped[Optional[int]]` to `PurchaseHistory` as a nullable FK → `recommendation_runs.id` ON DELETE SET NULL, with an index.
- `schemas/history.py`: Added `recommendation_run_id: Optional[int] = None` to `PurchaseCreate`, `PurchaseUpdate`, `PurchaseSummary`, and `PurchaseDetail`.
- `api/history.py`: `create_purchase` now passes `recommendation_run_id=body.recommendation_run_id` to the ORM object.
- `alembic/versions/20260318_01_*`: Migration adds the column + FK + index with idempotent guards (`_col_exists` check). Uses `batch_alter_table` (required for SQLite FK changes) with a named FK constraint.
- `tests/test_history.py`: 6 new tests in `TestPurchaseRecommendationLink` — backward compat (null/missing), FK persistence + DB verify, list/detail response shape, PRAGMA column check.

## Why

Purchases are logged but had no link to the recommendation run that suggested them. Without this, recommendation conversion cannot be measured. SC-70 is the foundational DB + API half; SC-78 is the frontend form half.

## Tricky Part

Alembic `batch_alter_table` on SQLite requires named FK constraints when using `create_foreign_key`. Anonymous `sa.ForeignKey(...)` in `add_column` raises `ValueError: Constraint must have a name`. Fixed by using `batch_op.create_foreign_key(name, ...)` separately.

## Test Count

153 tests passing (6 new in this ticket, up from 147).

## Next

- SC-71: Log 3 real brew sessions via BrewFeedbackForm (unblocked)
- SC-78: Update PurchaseForm to pass recommendationRunId prop (blocked on SC-70 ✓, now unblocked)
