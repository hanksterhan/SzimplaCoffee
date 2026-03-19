"""Tests for SC-50: recurring crawl scheduling and historical data collection."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.db import Base
from szimplacoffee.models import CrawlRun, Merchant
from szimplacoffee.services.scheduler import (
    DEFAULT_SCHEDULED_CRAWL_BATCH_SIZE,
    TIER_INTERVALS,
    get_crawl_schedule,
    get_merchants_due_for_crawl,
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


def _make_merchant(session: Session, *, name: str, tier: str = "B", is_active: bool = True) -> Merchant:
    m = Merchant(
        name=name,
        canonical_domain=f"{name.lower().replace(' ', '-')}.com",
        homepage_url=f"https://{name.lower().replace(' ', '-')}.com",
        platform_type="shopify",
        crawl_tier=tier,
        is_active=is_active,
    )
    session.add(m)
    session.flush()
    return m


def _make_crawl_run(session: Session, merchant: Merchant, *, status: str = "completed", age_hours: float = 0.0) -> CrawlRun:
    started_at = datetime.now(UTC) - timedelta(hours=age_hours)
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="scheduled_refresh",
        adapter_name="shopify",
        status=status,
        confidence=0.9,
        records_written=10,
        started_at=started_at,
        finished_at=started_at + timedelta(minutes=2),
    )
    session.add(run)
    session.flush()
    return run


# ---------------------------------------------------------------------------
# Tier interval constants
# ---------------------------------------------------------------------------

def test_tier_intervals_defined():
    assert TIER_INTERVALS["A"] == 6
    assert TIER_INTERVALS["B"] == 24
    assert TIER_INTERVALS["C"] == 7 * 24
    assert TIER_INTERVALS["D"] is None


# ---------------------------------------------------------------------------
# get_merchants_due_for_crawl
# ---------------------------------------------------------------------------

def test_never_crawled_merchant_is_always_due(db_session):
    m = _make_merchant(db_session, name="FreshRoast", tier="B")
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    assert any(d.id == m.id for d in due)


def test_recently_crawled_merchant_is_not_due(db_session):
    m = _make_merchant(db_session, name="RecentRoast", tier="B")
    _make_crawl_run(db_session, m, age_hours=1.0)  # 1h ago, threshold 24h
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    assert not any(d.id == m.id for d in due)


def test_overdue_merchant_is_due(db_session):
    m = _make_merchant(db_session, name="OldRoast", tier="B")
    _make_crawl_run(db_session, m, age_hours=25.0)  # past 24h B-tier threshold
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    assert any(d.id == m.id for d in due)


def test_tier_d_merchant_never_due(db_session):
    m = _make_merchant(db_session, name="ManualOnly", tier="D")
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    assert not any(d.id == m.id for d in due)


def test_inactive_merchant_not_returned(db_session):
    m = _make_merchant(db_session, name="Inactive", tier="B", is_active=False)
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    assert not any(d.id == m.id for d in due)


def test_failed_run_does_not_count_as_last_successful_crawl(db_session):
    """A failed crawl must not reset the due timer."""
    m = _make_merchant(db_session, name="FailedCrawl", tier="B")
    _make_crawl_run(db_session, m, status="failed", age_hours=1.0)
    db_session.commit()
    due = get_merchants_due_for_crawl(db_session)
    # Merchant has no successful crawl, so it should be due
    assert any(d.id == m.id for d in due)


def test_due_merchants_can_be_limited_to_a_small_serialized_batch(db_session):
    first = _make_merchant(db_session, name="FirstDue", tier="B")
    second = _make_merchant(db_session, name="SecondDue", tier="B")
    _make_crawl_run(db_session, first, age_hours=50.0)
    _make_crawl_run(db_session, second, age_hours=25.0)
    db_session.commit()

    due = get_merchants_due_for_crawl(
        db_session,
        limit=DEFAULT_SCHEDULED_CRAWL_BATCH_SIZE,
    )

    assert [merchant.id for merchant in due] == [first.id]


# ---------------------------------------------------------------------------
# get_crawl_schedule
# ---------------------------------------------------------------------------

def test_get_crawl_schedule_returns_all_active_merchants(db_session):
    m1 = _make_merchant(db_session, name="Alpha", tier="A")
    m2 = _make_merchant(db_session, name="Beta", tier="B")
    inactive = _make_merchant(db_session, name="Closed", tier="C", is_active=False)
    db_session.commit()
    schedule = get_crawl_schedule(db_session)
    ids = {row["merchant_id"] for row in schedule}
    assert m1.id in ids
    assert m2.id in ids
    assert inactive.id not in ids


def test_get_crawl_schedule_status_fresh(db_session):
    m = _make_merchant(db_session, name="Fresh", tier="B")
    _make_crawl_run(db_session, m, age_hours=1.0)
    db_session.commit()
    schedule = get_crawl_schedule(db_session)
    row = next(r for r in schedule if r["merchant_id"] == m.id)
    assert row["status"] == "fresh"


def test_get_crawl_schedule_status_overdue(db_session):
    m = _make_merchant(db_session, name="Overdue", tier="B")
    _make_crawl_run(db_session, m, age_hours=25.0)
    db_session.commit()
    schedule = get_crawl_schedule(db_session)
    row = next(r for r in schedule if r["merchant_id"] == m.id)
    assert row["status"] == "overdue"


def test_get_crawl_schedule_never_crawled(db_session):
    m = _make_merchant(db_session, name="Newbie", tier="C")
    db_session.commit()
    schedule = get_crawl_schedule(db_session)
    row = next(r for r in schedule if r["merchant_id"] == m.id)
    assert row["status"] == "never_crawled"
    assert row["is_due"] is True


def test_get_crawl_schedule_exposes_recent_reliability_signals(db_session):
    m = _make_merchant(db_session, name="SignalRoast", tier="B")
    completed = _make_crawl_run(db_session, m, status="completed", age_hours=30.0)
    completed.crawl_quality_score = 0.82
    failed = _make_crawl_run(db_session, m, status="failed", age_hours=2.0)
    failed.error_summary = "timeout"
    db_session.commit()

    schedule = get_crawl_schedule(db_session)
    row = next(r for r in schedule if r["merchant_id"] == m.id)

    assert row["recent_run_count"] == 2
    assert row["recent_failure_count"] == 1
    assert row["recent_success_rate"] == 0.5
    assert row["last_completed_crawl_quality_score"] == 0.82
    assert row["latest_run_status"] == "failed"
    assert row["latest_error_summary"] == "timeout"
