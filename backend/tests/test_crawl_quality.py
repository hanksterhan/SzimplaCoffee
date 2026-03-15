"""Tests for SC-51: layered crawl strategies and crawl-quality scoring."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.db import Base
from szimplacoffee.models import CrawlRun, Merchant
from szimplacoffee.services.crawlers import (
    STRATEGY_AGENTIC,
    STRATEGY_DOM,
    STRATEGY_FEED,
    STRATEGY_NONE,
    STRATEGY_STRUCTURED,
    CrawlSummary,
)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def _make_merchant(session: Session, *, name: str = "TestRoast", platform: str = "shopify") -> Merchant:
    m = Merchant(
        name=name,
        canonical_domain=f"{name.lower().replace(' ', '-')}.com",
        homepage_url=f"https://{name.lower().replace(' ', '-')}.com",
        platform_type=platform,
        crawl_tier="B",
    )
    session.add(m)
    session.flush()
    return m


# ---------------------------------------------------------------------------
# Strategy constant definitions
# ---------------------------------------------------------------------------

def test_strategy_constants_defined():
    assert STRATEGY_FEED == "feed"
    assert STRATEGY_STRUCTURED == "structured"
    assert STRATEGY_DOM == "dom"
    assert STRATEGY_AGENTIC == "agentic"
    assert STRATEGY_NONE == "none"


# ---------------------------------------------------------------------------
# CrawlSummary strategy fields and quality score
# ---------------------------------------------------------------------------

def test_crawl_summary_defaults_to_none_strategy():
    s = CrawlSummary(adapter_name="shopify", records_written=5, confidence=0.9)
    assert s.catalog_strategy == STRATEGY_NONE
    assert s.promo_strategy == STRATEGY_NONE
    assert s.shipping_strategy == STRATEGY_NONE
    assert s.metadata_strategy == STRATEGY_NONE


def test_crawl_quality_score_high_for_feed_strategy():
    """Feed strategy with high confidence should yield a score > 0.8."""
    s = CrawlSummary(
        adapter_name="shopify",
        records_written=20,
        confidence=0.95,
        catalog_strategy=STRATEGY_FEED,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
    )
    assert s.crawl_quality_score > 0.8


def test_crawl_quality_score_low_for_agentic_no_data():
    """Agentic-only strategy with low confidence should yield a score < 0.6."""
    s = CrawlSummary(
        adapter_name="agentic_catalog",
        records_written=3,
        confidence=0.4,
        catalog_strategy=STRATEGY_AGENTIC,
        promo_strategy=STRATEGY_NONE,
        shipping_strategy=STRATEGY_NONE,
        metadata_strategy=STRATEGY_NONE,
    )
    assert s.crawl_quality_score < 0.6


def test_crawl_quality_score_zero_for_none_strategy():
    """All-none strategies with 0 confidence should yield zero score."""
    s = CrawlSummary(
        adapter_name="generic",
        records_written=0,
        confidence=0.0,
        catalog_strategy=STRATEGY_NONE,
        promo_strategy=STRATEGY_NONE,
        shipping_strategy=STRATEGY_NONE,
        metadata_strategy=STRATEGY_NONE,
    )
    assert s.crawl_quality_score == 0.0


def test_crawl_quality_score_in_valid_range():
    for catalog in [STRATEGY_FEED, STRATEGY_STRUCTURED, STRATEGY_DOM, STRATEGY_AGENTIC, STRATEGY_NONE]:
        for confidence in [0.0, 0.5, 0.95]:
            s = CrawlSummary(
                adapter_name="shopify",
                records_written=10,
                confidence=confidence,
                catalog_strategy=catalog,
                promo_strategy=STRATEGY_DOM,
                shipping_strategy=STRATEGY_DOM,
                metadata_strategy=STRATEGY_STRUCTURED,
            )
            assert 0.0 <= s.crawl_quality_score <= 1.0, (
                f"score out of range for catalog={catalog} confidence={confidence}: {s.crawl_quality_score}"
            )


# ---------------------------------------------------------------------------
# CrawlRun model stores strategy fields
# ---------------------------------------------------------------------------

def test_crawl_run_stores_strategy_fields(db_session: Session):
    merchant = _make_merchant(db_session)
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name="shopify",
        status="completed",
        confidence=0.95,
        records_written=30,
        catalog_strategy=STRATEGY_FEED,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
        crawl_quality_score=0.88,
    )
    db_session.add(run)
    db_session.flush()

    fetched = db_session.get(CrawlRun, run.id)
    assert fetched is not None
    assert fetched.catalog_strategy == STRATEGY_FEED
    assert fetched.promo_strategy == STRATEGY_DOM
    assert fetched.shipping_strategy == STRATEGY_DOM
    assert fetched.metadata_strategy == STRATEGY_STRUCTURED
    assert abs(fetched.crawl_quality_score - 0.88) < 0.001


def test_crawl_run_defaults_strategy_to_none(db_session: Session):
    merchant = _make_merchant(db_session)
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name="generic",
        status="started",
        confidence=0.0,
        records_written=0,
    )
    db_session.add(run)
    db_session.flush()

    fetched = db_session.get(CrawlRun, run.id)
    assert fetched.catalog_strategy == "none"
    assert fetched.crawl_quality_score == 0.0


# ---------------------------------------------------------------------------
# Strategy ordering: feed > structured > dom > agentic
# ---------------------------------------------------------------------------

def test_feed_strategy_beats_agentic_strategy():
    """A feed-based crawl should score higher than an agentic crawl at same confidence."""
    feed_summary = CrawlSummary(
        adapter_name="shopify",
        records_written=20,
        confidence=0.8,
        catalog_strategy=STRATEGY_FEED,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
    )
    agentic_summary = CrawlSummary(
        adapter_name="agentic_catalog",
        records_written=20,
        confidence=0.8,
        catalog_strategy=STRATEGY_AGENTIC,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
    )
    assert feed_summary.crawl_quality_score > agentic_summary.crawl_quality_score
