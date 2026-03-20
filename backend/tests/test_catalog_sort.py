"""Tests for /api/v1/products/catalog sort parameter (SC-108)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from szimplacoffee.main import app
from szimplacoffee.models import (
    Merchant,
    MerchantQualityProfile,
    OfferSnapshot,
    Product,
    ProductVariant,
)
from szimplacoffee.db import get_session


def _make_merchant(db: Session, name: str, domain: str, quality_score: float) -> Merchant:
    m = Merchant(
        name=name,
        canonical_domain=domain,
        homepage_url=f"https://{domain}",
        platform_type="shopify",
        country_code="US",
        is_active=True,
        crawl_tier="B",
        trust_tier="approved",
    )
    db.add(m)
    db.flush()
    qp = MerchantQualityProfile(
        merchant_id=m.id,
        overall_quality_score=quality_score,
        freshness_transparency_score=quality_score,
    )
    db.add(qp)
    db.flush()
    return m


def _make_product_with_offer(
    db: Session,
    merchant: Merchant,
    name: str,
    price_cents: int,
    is_available: bool = True,
) -> Product:
    p = Product(
        merchant_id=merchant.id,
        external_product_id=f"ext-{merchant.canonical_domain}-{name}",
        name=name,
        product_url=f"https://{merchant.canonical_domain}/{name}",
        is_active=True,
        product_category="coffee",
    )
    db.add(p)
    db.flush()
    v = ProductVariant(
        product_id=p.id,
        external_variant_id=f"var-{merchant.canonical_domain}-{name}",
        label="12oz",
        weight_grams=340,
        is_whole_bean=True,
        is_available=is_available,
    )
    db.add(v)
    db.flush()
    offer = OfferSnapshot(
        variant_id=v.id,
        price_cents=price_cents,
        is_available=is_available,
        is_on_sale=False,
        source_url=f"https://{merchant.canonical_domain}/{name}",
    )
    db.add(offer)
    db.flush()
    return p


@pytest.fixture()
def catalog_sort_client(tmp_path):
    """Client wired to an in-memory SQLite DB with known quality-score merchants."""
    import os

    db_path = tmp_path / "test_catalog_sort.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Re-create engine/tables with the test URL
    from sqlalchemy import create_engine
    from szimplacoffee.models import Base

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session

    # Seed merchants and products
    with TestingSessionLocal() as seed_session:
        low_q = _make_merchant(seed_session, "LowQuality", "low-quality.test", 0.3)
        high_q = _make_merchant(seed_session, "HighQuality", "high-quality.test", 0.9)
        mid_q = _make_merchant(seed_session, "MidQuality", "mid-quality.test", 0.6)

        _make_product_with_offer(seed_session, low_q, "Cheap Coffee", 1000)
        _make_product_with_offer(seed_session, high_q, "Premium Coffee", 2500)
        _make_product_with_offer(seed_session, mid_q, "Medium Coffee", 1800)
        # Add a pricey product from low-quality merchant
        _make_product_with_offer(seed_session, low_q, "Expensive Low Quality", 3000)
        seed_session.commit()

    client = TestClient(app)
    yield client

    app.dependency_overrides.pop(get_session, None)
    engine.dispose()


def test_catalog_sort_quality_returns_high_quality_merchants_first(catalog_sort_client):
    """sort=quality should return HighQuality merchant products before LowQuality."""
    resp = catalog_sort_client.get("/api/v1/products/catalog?sort=quality&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert len(items) >= 3

    merchant_names = [item["merchant_name"] for item in items]
    # HighQuality (0.9) should appear before LowQuality (0.3)
    assert "HighQuality" in merchant_names
    assert "LowQuality" in merchant_names
    high_idx = next(i for i, n in enumerate(merchant_names) if n == "HighQuality")
    low_idx = next(i for i, n in enumerate(merchant_names) if n == "LowQuality")
    assert high_idx < low_idx, (
        f"Expected HighQuality (score=0.9) to appear before LowQuality (score=0.3), "
        f"got indexes {high_idx} vs {low_idx} in {merchant_names}"
    )


def test_catalog_sort_price_low_returns_cheapest_first(catalog_sort_client):
    """sort=price_low should return cheaper products first."""
    resp = catalog_sort_client.get("/api/v1/products/catalog?sort=price_low&limit=10")
    assert resp.status_code == 200
    items = resp.json()["items"]
    prices = [item.get("latest_price_cents") for item in items if item.get("latest_price_cents")]
    # Should be non-decreasing
    assert prices == sorted(prices), f"Expected ascending prices, got {prices}"


def test_catalog_sort_price_high_returns_expensive_first(catalog_sort_client):
    """sort=price_high should return more expensive products first."""
    resp = catalog_sort_client.get("/api/v1/products/catalog?sort=price_high&limit=10")
    assert resp.status_code == 200
    items = resp.json()["items"]
    prices = [item.get("latest_price_cents") for item in items if item.get("latest_price_cents")]
    assert prices == sorted(prices, reverse=True), f"Expected descending prices, got {prices}"


def test_catalog_sort_default_is_quality(catalog_sort_client):
    """Default sort (no sort param) should behave the same as sort=quality."""
    resp_default = catalog_sort_client.get("/api/v1/products/catalog?limit=10")
    resp_quality = catalog_sort_client.get("/api/v1/products/catalog?sort=quality&limit=10")
    assert resp_default.status_code == 200
    assert resp_quality.status_code == 200
    names_default = [item["name"] for item in resp_default.json()["items"]]
    names_quality = [item["name"] for item in resp_quality.json()["items"]]
    assert names_default == names_quality, (
        f"Default and explicit quality sort should return same order.\n"
        f"Default: {names_default}\nQuality: {names_quality}"
    )


def test_catalog_sort_freshness(catalog_sort_client):
    """sort=freshness should return 200 and a non-empty list."""
    resp = catalog_sort_client.get("/api/v1/products/catalog?sort=freshness&limit=10")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0


def test_catalog_sort_has_more_and_cursor(catalog_sort_client):
    """Cursor pagination should work with the catalog endpoint."""
    resp1 = catalog_sort_client.get("/api/v1/products/catalog?sort=quality&limit=2")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["has_more"] is True
    assert data1["next_cursor"] is not None

    resp2 = catalog_sort_client.get(
        f"/api/v1/products/catalog?sort=quality&limit=2&cursor={data1['next_cursor']}"
    )
    assert resp2.status_code == 200
    items2 = resp2.json()["items"]
    assert len(items2) > 0
    # Items from page 2 should not overlap with page 1
    names1 = {item["name"] for item in data1["items"]}
    names2 = {item["name"] for item in items2}
    assert names1.isdisjoint(names2), f"Page 1 and page 2 overlap: {names1 & names2}"
