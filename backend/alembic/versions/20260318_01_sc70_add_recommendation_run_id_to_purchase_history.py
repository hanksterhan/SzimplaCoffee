"""SC-70: add recommendation_run_id to purchase_history.

Revision ID: 20260318_01
Revises: 20260315_02
Create Date: 2026-03-18 14:49:00.000000

Adds optional recommendation_run_id FK to purchase_history table so purchases
can be linked back to the recommendation run that suggested them.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260318_01"
down_revision = "20260315_02"
branch_labels = None
depends_on = None


def _col_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _col_exists(inspector, "purchase_history", "recommendation_run_id"):
        with op.batch_alter_table("purchase_history") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "recommendation_run_id",
                    sa.Integer(),
                    nullable=True,
                )
            )
            batch_op.create_foreign_key(
                "fk_purchase_history_recommendation_run_id",
                "recommendation_runs",
                ["recommendation_run_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index(
                "ix_purchase_history_recommendation_run_id",
                ["recommendation_run_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _col_exists(inspector, "purchase_history", "recommendation_run_id"):
        with op.batch_alter_table("purchase_history") as batch_op:
            batch_op.drop_index("ix_purchase_history_recommendation_run_id")
            batch_op.drop_constraint(
                "fk_purchase_history_recommendation_run_id", type_="foreignkey"
            )
            batch_op.drop_column("recommendation_run_id")
