"""SC-79: DE1 Visualizer bridge — de1_bridge_state table + brew_feedback telemetry columns.

Revision ID: 20260318_02
Revises: 20260318_01
Create Date: 2026-03-18 16:00:00.000000

Changes:
1. Create de1_bridge_state table (singleton row tracking last poll state).
2. Add telemetry columns to brew_feedback: dose_grams, yield_grams, brew_time_seconds,
   water_temp_c, machine, product_id (FK→products), visualizer_shot_id (unique).
3. Make brew_feedback.purchase_id nullable (DE1-imported shots have no purchase).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260318_02"
down_revision = "20260318_01"
branch_labels = None
depends_on = None


def _col_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Create de1_bridge_state table
    if not _table_exists(inspector, "de1_bridge_state"):
        op.create_table(
            "de1_bridge_state",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("last_seen_shot_id", sa.String(128), nullable=True),
            sa.Column("last_poll_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("shots_imported", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("auto_match", sa.Boolean(), nullable=False, server_default="1"),
        )

    # 2. Add telemetry columns to brew_feedback + make purchase_id nullable
    brew_feedback_cols_to_add = [
        ("dose_grams", sa.Column("dose_grams", sa.Float(), nullable=True)),
        ("yield_grams", sa.Column("yield_grams", sa.Float(), nullable=True)),
        ("brew_time_seconds", sa.Column("brew_time_seconds", sa.Float(), nullable=True)),
        ("water_temp_c", sa.Column("water_temp_c", sa.Float(), nullable=True)),
        ("machine", sa.Column("machine", sa.String(64), nullable=False, server_default="")),
        ("product_id", sa.Column("product_id", sa.Integer(), nullable=True)),
        ("visualizer_shot_id", sa.Column("visualizer_shot_id", sa.String(128), nullable=True)),
    ]

    with op.batch_alter_table("brew_feedback") as batch_op:
        for col_name, col_def in brew_feedback_cols_to_add:
            if not _col_exists(inspector, "brew_feedback", col_name):
                batch_op.add_column(col_def)

        # Add FK for product_id if column was just added
        if not _col_exists(inspector, "brew_feedback", "product_id"):
            batch_op.create_foreign_key(
                "fk_brew_feedback_product_id",
                "products",
                ["product_id"],
                ["id"],
            )

        # Make purchase_id nullable (SQLite requires batch_alter recreate)
        batch_op.alter_column(
            "purchase_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

        # Unique constraint on visualizer_shot_id
        if not _col_exists(inspector, "brew_feedback", "visualizer_shot_id"):
            batch_op.create_unique_constraint(
                "uq_brew_feedback_visualizer_shot_id",
                ["visualizer_shot_id"],
            )

    # Add unique index on visualizer_shot_id separately (idempotent)
    try:
        op.create_index(
            "ix_brew_feedback_visualizer_shot_id",
            "brew_feedback",
            ["visualizer_shot_id"],
            unique=True,
        )
    except Exception:  # noqa: BLE001
        pass  # already exists


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "de1_bridge_state"):
        op.drop_table("de1_bridge_state")

    brew_cols = {c["name"] for c in inspector.get_columns("brew_feedback")}
    cols_to_drop = [
        "dose_grams", "yield_grams", "brew_time_seconds", "water_temp_c",
        "machine", "product_id", "visualizer_shot_id",
    ]
    with op.batch_alter_table("brew_feedback") as batch_op:
        batch_op.alter_column("purchase_id", existing_type=sa.Integer(), nullable=False)
        for col in cols_to_drop:
            if col in brew_cols:
                batch_op.drop_column(col)
