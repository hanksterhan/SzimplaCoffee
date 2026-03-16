"""SC-52/53/54: add merchant watch/tier columns, crawl quality, deal facts.

Revision ID: 20260315_02
Revises: 20260315_01
Create Date: 2026-03-15 23:30:00.000000

Covers all schema additions since SC-46 migration:
  - merchants: is_watched, crawl_tier, trust_tier
  - crawl_runs: catalog_strategy, promo_strategy, shipping_strategy, metadata_strategy, crawl_quality_score
  - recommendation_runs: wait_recommendation
  - variant_deal_facts table (new, SC-49)
  - merchant_field_patterns table (new, SC-47)
  - product_metadata_overrides table (new, SC-47)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260315_02"
down_revision = "20260315_01"
branch_labels = None
depends_on = None


def _col_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _index_exists(inspector, table: str, index: str) -> bool:
    return index in {i["name"] for i in inspector.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── merchants ────────────────────────────────────────────────────────────
    if _table_exists(inspector, "merchants"):
        with op.batch_alter_table("merchants") as batch_op:
            if not _col_exists(inspector, "merchants", "is_watched"):
                batch_op.add_column(sa.Column("is_watched", sa.Boolean(), nullable=False, server_default="0"))
            if not _col_exists(inspector, "merchants", "crawl_tier"):
                batch_op.add_column(sa.Column("crawl_tier", sa.String(1), nullable=False, server_default="B"))
            if not _col_exists(inspector, "merchants", "trust_tier"):
                batch_op.add_column(sa.Column("trust_tier", sa.String(32), nullable=False, server_default="candidate"))

        # indexes (created outside batch to avoid duplicate errors)
        if not _index_exists(inspector, "merchants", "ix_merchants_is_watched"):
            op.create_index("ix_merchants_is_watched", "merchants", ["is_watched"])
        if not _index_exists(inspector, "merchants", "ix_merchants_crawl_tier"):
            op.create_index("ix_merchants_crawl_tier", "merchants", ["crawl_tier"])
        if not _index_exists(inspector, "merchants", "ix_merchants_trust_tier"):
            op.create_index("ix_merchants_trust_tier", "merchants", ["trust_tier"])

    # ── crawl_runs ───────────────────────────────────────────────────────────
    if _table_exists(inspector, "crawl_runs"):
        with op.batch_alter_table("crawl_runs") as batch_op:
            if not _col_exists(inspector, "crawl_runs", "catalog_strategy"):
                batch_op.add_column(sa.Column("catalog_strategy", sa.String(32), nullable=False, server_default="none"))
            if not _col_exists(inspector, "crawl_runs", "promo_strategy"):
                batch_op.add_column(sa.Column("promo_strategy", sa.String(32), nullable=False, server_default="none"))
            if not _col_exists(inspector, "crawl_runs", "shipping_strategy"):
                batch_op.add_column(sa.Column("shipping_strategy", sa.String(32), nullable=False, server_default="none"))
            if not _col_exists(inspector, "crawl_runs", "metadata_strategy"):
                batch_op.add_column(sa.Column("metadata_strategy", sa.String(32), nullable=False, server_default="none"))
            if not _col_exists(inspector, "crawl_runs", "crawl_quality_score"):
                batch_op.add_column(sa.Column("crawl_quality_score", sa.Float(), nullable=False, server_default="0.0"))

    # ── recommendation_runs ──────────────────────────────────────────────────
    if _table_exists(inspector, "recommendation_runs"):
        with op.batch_alter_table("recommendation_runs") as batch_op:
            if not _col_exists(inspector, "recommendation_runs", "wait_recommendation"):
                batch_op.add_column(sa.Column("wait_recommendation", sa.Boolean(), nullable=False, server_default="0"))

    # ── merchant_field_patterns (new table, SC-47) ───────────────────────────
    if not _table_exists(inspector, "merchant_field_patterns"):
        op.create_table(
            "merchant_field_patterns",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
            sa.Column("field_name", sa.String(64), nullable=False, index=True),
            sa.Column("pattern", sa.Text(), nullable=False),
            sa.Column("normalized_value", sa.String(255), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="0.95"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("merchant_id", "field_name", "pattern", name="uq_merchant_field_patterns"),
        )

    # ── product_metadata_overrides (new table, SC-47) ────────────────────────
    if not _table_exists(inspector, "product_metadata_overrides"):
        op.create_table(
            "product_metadata_overrides",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("merchant_id", sa.Integer(), sa.ForeignKey("merchants.id"), nullable=False, index=True),
            sa.Column("external_product_id", sa.String(128), nullable=False),
            sa.Column("field_name", sa.String(64), nullable=False),
            sa.Column("override_value", sa.Text(), nullable=False),
            sa.Column("source", sa.String(64), nullable=False, server_default="manual"),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("merchant_id", "external_product_id", "field_name", name="uq_product_metadata_overrides"),
        )

    # ── variant_deal_facts (new table, SC-49) ────────────────────────────────
    if not _table_exists(inspector, "variant_deal_facts"):
        op.create_table(
            "variant_deal_facts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id"), nullable=False, unique=True, index=True),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, index=True),
            sa.Column("offer_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("distinct_offer_days", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_price_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("baseline_7d_cents", sa.Integer(), nullable=True),
            sa.Column("baseline_30d_cents", sa.Integer(), nullable=True),
            sa.Column("historical_low_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("historical_high_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("compare_at_discount_percent", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("price_drop_7d_percent", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("price_drop_30d_percent", sa.Float(), nullable=False, server_default="0.0"),
        )


def downgrade() -> None:
    # Drop new tables
    op.drop_table("variant_deal_facts")
    op.drop_table("product_metadata_overrides")
    op.drop_table("merchant_field_patterns")

    # Drop added columns (batch mode required for SQLite)
    with op.batch_alter_table("recommendation_runs") as batch_op:
        batch_op.drop_column("wait_recommendation")

    with op.batch_alter_table("crawl_runs") as batch_op:
        batch_op.drop_column("crawl_quality_score")
        batch_op.drop_column("metadata_strategy")
        batch_op.drop_column("shipping_strategy")
        batch_op.drop_column("promo_strategy")
        batch_op.drop_column("catalog_strategy")

    with op.batch_alter_table("merchants") as batch_op:
        batch_op.drop_column("trust_tier")
        batch_op.drop_column("crawl_tier")
        batch_op.drop_column("is_watched")
