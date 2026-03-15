"""SC-46 add normalized product metadata columns.

Revision ID: 20260315_01
Revises:
Create Date: 2026-03-15 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from szimplacoffee.db import Base
from szimplacoffee.models import Product  # noqa: F401


revision = "20260315_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "products" not in inspector.get_table_names():
        Base.metadata.create_all(bind)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("products")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("products")}

    with op.batch_alter_table("products") as batch_op:
        if "origin_country" not in existing_columns:
            batch_op.add_column(sa.Column("origin_country", sa.String(length=128), nullable=True))
        if "origin_region" not in existing_columns:
            batch_op.add_column(sa.Column("origin_region", sa.String(length=128), nullable=True))
        if "process_family" not in existing_columns:
            batch_op.add_column(
                sa.Column("process_family", sa.String(length=32), nullable=False, server_default="unknown")
            )
        if "roast_level" not in existing_columns:
            batch_op.add_column(
                sa.Column("roast_level", sa.String(length=32), nullable=False, server_default="unknown")
            )
        if "metadata_confidence" not in existing_columns:
            batch_op.add_column(
                sa.Column("metadata_confidence", sa.Float(), nullable=False, server_default="0")
            )
        if "metadata_source" not in existing_columns:
            batch_op.add_column(
                sa.Column("metadata_source", sa.String(length=32), nullable=False, server_default="unknown")
            )

    if "ix_products_origin_country" not in existing_indexes:
        op.create_index("ix_products_origin_country", "products", ["origin_country"], unique=False)
    if "ix_products_process_family" not in existing_indexes:
        op.create_index("ix_products_process_family", "products", ["process_family"], unique=False)
    if "ix_products_roast_level" not in existing_indexes:
        op.create_index("ix_products_roast_level", "products", ["roast_level"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "products" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("products")}
    existing_indexes = {index["name"] for index in inspector.get_indexes("products")}

    if "ix_products_roast_level" in existing_indexes:
        op.drop_index("ix_products_roast_level", table_name="products")
    if "ix_products_process_family" in existing_indexes:
        op.drop_index("ix_products_process_family", table_name="products")
    if "ix_products_origin_country" in existing_indexes:
        op.drop_index("ix_products_origin_country", table_name="products")

    with op.batch_alter_table("products") as batch_op:
        if "metadata_source" in existing_columns:
            batch_op.drop_column("metadata_source")
        if "metadata_confidence" in existing_columns:
            batch_op.drop_column("metadata_confidence")
        if "roast_level" in existing_columns:
            batch_op.drop_column("roast_level")
        if "process_family" in existing_columns:
            batch_op.drop_column("process_family")
        if "origin_region" in existing_columns:
            batch_op.drop_column("origin_region")
        if "origin_country" in existing_columns:
            batch_op.drop_column("origin_country")
