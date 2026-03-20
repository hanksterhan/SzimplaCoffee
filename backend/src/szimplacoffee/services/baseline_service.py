"""SC-107: Variant price baseline computation service.

Computes per-variant price baselines (median, min, max) from OfferSnapshot history
over a configurable rolling window (default: 90 days). Results are upserted into
VariantPriceBaseline for use by the recommendation engine (SC-109 deal-scoring).
"""
from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Merchant, OfferSnapshot, ProductVariant, VariantPriceBaseline


def compute_variant_baselines(
    db: Session,
    merchant_id: Optional[int] = None,
    window_days: int = 90,
) -> dict[str, int]:
    """Compute and upsert price baselines for all variants (or one merchant's variants).

    Args:
        db: SQLAlchemy session.
        merchant_id: If set, only process variants belonging to this merchant.
        window_days: Rolling history window in days (default 90).

    Returns:
        Dict with keys 'computed', 'skipped' (no snapshots), 'total_variants'.
    """
    cutoff = datetime.now(UTC) - timedelta(days=window_days)

    # Build base query for variant IDs to process
    if merchant_id is not None:
        # Verify merchant exists
        merchant = db.get(Merchant, merchant_id)
        if merchant is None:
            raise ValueError(f"Merchant {merchant_id} not found")
        variant_ids_query = (
            select(ProductVariant.id)
            .join(ProductVariant.product)
            .where(ProductVariant.product.has(merchant_id=merchant_id))
        )
        variant_ids = list(db.scalars(variant_ids_query).all())
    else:
        variant_ids = list(db.scalars(select(ProductVariant.id)).all())

    computed = 0
    skipped = 0

    for variant_id in variant_ids:
        # Fetch offer prices within the window
        prices = list(
            db.scalars(
                select(OfferSnapshot.price_cents)
                .where(OfferSnapshot.variant_id == variant_id)
                .where(OfferSnapshot.observed_at >= cutoff)
                .order_by(OfferSnapshot.observed_at.asc())
            ).all()
        )

        if not prices:
            skipped += 1
            continue

        median_cents = int(statistics.median(prices))
        min_cents = min(prices)
        max_cents = max(prices)

        # Upsert: check for existing baseline
        existing = db.scalar(
            select(VariantPriceBaseline).where(VariantPriceBaseline.variant_id == variant_id)
        )
        now = datetime.now(UTC)

        if existing is not None:
            existing.median_price_cents = median_cents
            existing.min_price_cents = min_cents
            existing.max_price_cents = max_cents
            existing.sample_count = len(prices)
            existing.baseline_window_days = window_days
            existing.computed_at = now
        else:
            baseline = VariantPriceBaseline(
                variant_id=variant_id,
                median_price_cents=median_cents,
                min_price_cents=min_cents,
                max_price_cents=max_cents,
                sample_count=len(prices),
                baseline_window_days=window_days,
                computed_at=now,
            )
            db.add(baseline)

        computed += 1

    db.flush()

    return {
        "computed": computed,
        "skipped": skipped,
        "total_variants": len(variant_ids),
    }
