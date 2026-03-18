"""Tests for SC-74: crawl health fields on merchant list API."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.api.merchants import router as merchants_router
from szimplacoffee.db import Base, get_session
from szimplacoffee.models import CrawlRun, Merchant, Product


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture()
def client(db_engine):
    app = FastAPI()
    app.include_router(merchants_router)

    def override_get_session():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def _make_merchant(session: Session, *, name: str = "TestRoast", **kwargs) -> Merchant:
    defaults = dict(
        name=name,
        canonical_domain=f"{name.lower().replace(' ', '')}.com",
        homepage_url=f"https://{name.lower().replace(' ', '')}.com",
        platform_type="shopify",
        crawl_tier="B",
        trust_tier="candidate",
    )
    defaults.update(kwargs)
    m = Merchant(**defaults)
    session.add(m)
    session.flush()
    return m


def _make_product(
    session: Session,
    merchant: Merchant,
    *,
    origin_country: str | None = None,
    process_family: str = "unknown",
    roast_level: str = "unknown",
) -> Product:
    count = session.query(Product).count()
    p = Product(
        merchant_id=merchant.id,
        external_product_id=f"p-{merchant.id}-{count}",
        name="Test Coffee",
        product_url=f"https://{merchant.canonical_domain}/products/test-{count}",
        product_category="coffee",
        origin_country=origin_country,
        process_family=process_family,
        roast_level=roast_level,
    )
    session.add(p)
    session.flush()
    return p


def _make_crawl_run(
    session: Session,
    merchant: Merchant,
    *,
    status: str = "completed",
    minutes_ago: int = 60,
) -> CrawlRun:
    now = datetime.now(UTC)
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name="shopify",
        started_at=now - timedelta(minutes=minutes_ago),
        finished_at=now - timedelta(minutes=minutes_ago - 5),
        status=status,
        confidence=0.9,
        records_written=10,
    )
    session.add(run)
    session.flush()
    return run


def test_merchant_list_includes_crawl_health_fields(client, db_session):
    """GET /merchants returns last_crawl_at, crawl_success, product_count, metadata_pct."""
    m = _make_merchant(db_session, name="BlueMtn")
    _make_crawl_run(db_session, m)
    _make_product(db_session, m, origin_country="Ethiopia")
    _make_product(db_session, m)  # no metadata
    db_session.commit()

    resp = client.get("/merchants")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    item = items[0]

    assert item["last_crawl_at"] is not None
    assert item["crawl_success"] is True
    assert item["product_count"] == 2
    assert item["metadata_pct"] == 50.0


def test_merchant_list_no_crawl_run(client, db_session):
    """Merchant with no crawl run returns null last_crawl_at, null crawl_success."""
    _make_merchant(db_session, name="NewRoast")
    db_session.commit()

    resp = client.get("/merchants")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    item = items[0]

    assert item["last_crawl_at"] is None
    assert item["crawl_success"] is None
    assert item["product_count"] == 0
    assert item["metadata_pct"] == 0.0


def test_merchant_list_failed_crawl(client, db_session):
    """Merchant with failed crawl returns crawl_success=False."""
    m = _make_merchant(db_session, name="FailRoast")
    _make_crawl_run(db_session, m, status="failed")
    db_session.commit()

    resp = client.get("/merchants")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["crawl_success"] is False


def test_metadata_pct_counts_process_and_roast(client, db_session):
    """metadata_pct includes products with process_family or roast_level filled."""
    m = _make_merchant(db_session, name="MetaRoast")
    _make_crawl_run(db_session, m)
    _make_product(db_session, m, process_family="washed")
    _make_product(db_session, m, roast_level="light")
    _make_product(db_session, m)  # no metadata
    db_session.commit()

    resp = client.get("/merchants")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["product_count"] == 3
    assert round(item["metadata_pct"], 1) == pytest.approx(66.7, abs=0.2)


def test_multiple_crawl_runs_uses_latest(client, db_session):
    """Only the most recent crawl run's data is used for last_crawl_at."""
    m = _make_merchant(db_session, name="MultiCrawl")
    _make_crawl_run(db_session, m, status="failed", minutes_ago=120)
    _make_crawl_run(db_session, m, status="completed", minutes_ago=30)
    db_session.commit()

    resp = client.get("/merchants")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    # Latest run is the completed one
    assert item["crawl_success"] is True


def test_enrich_merchant_summaries_watchlist(db_session):
    """_enrich_merchant_summaries returns crawl health for watched merchants (SC-74)."""
    from szimplacoffee.api.merchants import _enrich_merchant_summaries

    m = _make_merchant(db_session, name="WatchRoast", is_watched=True)
    _make_crawl_run(db_session, m)
    _make_product(db_session, m, origin_country="Colombia")
    db_session.commit()

    summaries = _enrich_merchant_summaries(db_session, [m])
    assert len(summaries) == 1
    s = summaries[0]
    assert s.product_count == 1
    assert s.metadata_pct == 100.0
    assert s.crawl_success is True
    assert s.last_crawl_at is not None
