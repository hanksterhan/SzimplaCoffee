"""SC-104: Add description_text column to products table.

Revision ID: 20260320_01
Revises: 20260318_02
Create Date: 2026-03-20 06:23:00.000000

Changes:
1. Add nullable TEXT column `description_text` to products table.
   Stores plain text stripped from body_html fetched during crawls.
   Used by coffee_parser backfill to improve origin/process coverage.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260320_01"
down_revision = "20260318_02"
branch_labels = None
depends_on = None


def _col_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _col_exists(inspector, "products", "description_text"):
        op.add_column("products", sa.Column("description_text", sa.Text(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _col_exists(inspector, "products", "description_text"):
        op.drop_column("products", "description_text")
