"""SC-107: Add variant_price_baselines table for historical price baselines.

Revision ID: 20260320_02
Revises: 20260320_01
Create Date: 2026-03-20 09:01:00.000000

Changes:
1. Add variant_price_baselines table: one row per variant storing
   median/min/max price cents, sample count, window days, computed_at.
   Used by recommendation engine for deal-score computation (SC-109).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260320_02"
down_revision = "20260320_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use CREATE TABLE IF NOT EXISTS to handle the case where init_db()
    # (Base.metadata.create_all) already created this table before the migration ran.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS variant_price_baselines (
            id INTEGER NOT NULL,
            variant_id INTEGER NOT NULL,
            median_price_cents INTEGER NOT NULL,
            min_price_cents INTEGER NOT NULL,
            max_price_cents INTEGER NOT NULL,
            sample_count INTEGER DEFAULT 0 NOT NULL,
            baseline_window_days INTEGER DEFAULT 90 NOT NULL,
            computed_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(variant_id) REFERENCES product_variants (id),
            UNIQUE (variant_id)
        )
        """
    )
    # Create indexes idempotently (SQLite will ignore these if they exist)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_variant_price_baselines_variant_id "
        "ON variant_price_baselines (variant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_variant_price_baselines_computed_at "
        "ON variant_price_baselines (computed_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_variant_price_baselines_computed_at")
    op.execute("DROP INDEX IF EXISTS ix_variant_price_baselines_variant_id")
    op.drop_table("variant_price_baselines")
