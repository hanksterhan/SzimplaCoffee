"""SC-107: Tests for baseline_service.compute_variant_baselines()."""
from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.db import Base
from szimplacoffee.models import Merchant, OfferSnapshot, Product, ProductVariant, VariantPriceBaseline
from szimplacoffee.services.baseline_service import compute_variant_baselines


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db() -> Session:
    """In-memory SQLite session with all tables created."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _merchant(db: Session) -> Merchant:
    m = Merchant(
        name="Test Roaster",
        canonical_domain="test.com",
        homepage_url="https://test.com",
    )
    db.add(m)
    db.flush()
    return m


_prod_counter = 0


def _product(db: Session, merchant: Merchant) -> Product:
    global _prod_counter
    _prod_counter += 1
    p = Product(
        merchant_id=merchant.id,
        external_product_id=f"ext-{merchant.id}-{_prod_counter}",
        name="Test Coffee",
        product_url="https://test.com/coffee",
        image_url="",
        origin_text="",
        process_text="",
        tasting_notes_text="",
        roast_cues="",
        variety_text="",
        product_category="coffee",
    )
    db.add(p)
    db.flush()
    return p


def _variant(db: Session, product: Product) -> ProductVariant:
    v = ProductVariant(
        product_id=product.id,
        external_variant_id="v1",
        label="12oz",
        weight_grams=340,
    )
    db.add(v)
    db.flush()
    return v


def _snapshot(db: Session, variant: ProductVariant, price_cents: int, days_ago: int = 1) -> OfferSnapshot:
    o = OfferSnapshot(
        variant_id=variant.id,
        observed_at=datetime.now(UTC) - timedelta(days=days_ago),
        price_cents=price_cents,
        source_url="https://test.com",
    )
    db.add(o)
    db.flush()
    return o


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNoHistory:
    def test_no_snapshots_no_baseline_created(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        _variant(db, p)

        result = compute_variant_baselines(db)

        assert result["total_variants"] == 1
        assert result["computed"] == 0
        assert result["skipped"] == 1

        count = db.query(VariantPriceBaseline).count()
        assert count == 0


class TestSingleSnapshot:
    def test_single_snapshot_median_equals_min_equals_max(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        _snapshot(db, v, price_cents=1500, days_ago=5)

        result = compute_variant_baselines(db)

        assert result["computed"] == 1
        assert result["skipped"] == 0

        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        assert baseline.median_price_cents == 1500
        assert baseline.min_price_cents == 1500
        assert baseline.max_price_cents == 1500
        assert baseline.sample_count == 1
        assert baseline.baseline_window_days == 90


class TestMultipleSnapshots:
    def test_multiple_snapshots_correct_median(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        prices = [1800, 1600, 1400, 1700, 1500]
        for i, price in enumerate(prices):
            _snapshot(db, v, price_cents=price, days_ago=i + 1)

        result = compute_variant_baselines(db)

        assert result["computed"] == 1
        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        expected_median = int(statistics.median(prices))
        assert baseline.median_price_cents == expected_median
        assert baseline.min_price_cents == min(prices)
        assert baseline.max_price_cents == max(prices)
        assert baseline.sample_count == len(prices)

    def test_odd_number_of_snapshots_median(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        prices = [1000, 2000, 1500]
        for i, price in enumerate(prices):
            _snapshot(db, v, price_cents=price, days_ago=i + 1)

        compute_variant_baselines(db)

        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        assert baseline.median_price_cents == 1500  # median of [1000, 1500, 2000]

    def test_even_number_of_snapshots_median(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        prices = [1000, 2000]
        for i, price in enumerate(prices):
            _snapshot(db, v, price_cents=price, days_ago=i + 1)

        compute_variant_baselines(db)

        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        assert baseline.median_price_cents == 1500  # int(median([1000, 2000])) = 1500


class TestWindowCutoff:
    def test_90_day_window_excludes_old_snapshots(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        # Within window
        _snapshot(db, v, price_cents=1500, days_ago=10)
        _snapshot(db, v, price_cents=1600, days_ago=30)
        # Outside window
        _snapshot(db, v, price_cents=9999, days_ago=91)
        _snapshot(db, v, price_cents=9999, days_ago=120)

        compute_variant_baselines(db, window_days=90)

        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        assert baseline.sample_count == 2
        assert baseline.max_price_cents == 1600
        assert 9999 not in [baseline.min_price_cents, baseline.max_price_cents]

    def test_custom_window_days_respected(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        _snapshot(db, v, price_cents=1200, days_ago=3)
        _snapshot(db, v, price_cents=1400, days_ago=8)  # outside 7-day window

        compute_variant_baselines(db, window_days=7)

        baseline = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).one()
        assert baseline.sample_count == 1
        assert baseline.baseline_window_days == 7


class TestUpsert:
    def test_recompute_updates_existing_baseline(self, db: Session) -> None:
        m = _merchant(db)
        p = _product(db, m)
        v = _variant(db, p)
        _snapshot(db, v, price_cents=1500, days_ago=1)

        compute_variant_baselines(db)
        db.commit()

        # Add a new snapshot at a very different price
        _snapshot(db, v, price_cents=2000, days_ago=2)
        compute_variant_baselines(db)
        db.commit()

        baselines = db.query(VariantPriceBaseline).filter_by(variant_id=v.id).all()
        assert len(baselines) == 1  # no duplicate rows
        baseline = baselines[0]
        assert baseline.sample_count == 2


class TestMerchantFilter:
    def test_merchant_id_filter_only_processes_that_merchants_variants(self, db: Session) -> None:
        m1 = _merchant(db)
        m2 = Merchant(name="Other Roaster", canonical_domain="other.com", homepage_url="https://other.com")
        db.add(m2)
        db.flush()

        p1 = _product(db, m1)
        p2 = _product(db, m2)
        v1 = _variant(db, p1)
        v2 = ProductVariant(product_id=p2.id, external_variant_id="v1", label="12oz", weight_grams=340)
        db.add(v2)
        db.flush()

        _snapshot(db, v1, price_cents=1500)
        _snapshot(db, v2, price_cents=2000)

        result = compute_variant_baselines(db, merchant_id=m1.id)

        assert result["total_variants"] == 1
        assert result["computed"] == 1

        assert db.query(VariantPriceBaseline).filter_by(variant_id=v1.id).count() == 1
        assert db.query(VariantPriceBaseline).filter_by(variant_id=v2.id).count() == 0

    def test_invalid_merchant_id_raises(self, db: Session) -> None:
        with pytest.raises(ValueError, match="not found"):
            compute_variant_baselines(db, merchant_id=99999)
