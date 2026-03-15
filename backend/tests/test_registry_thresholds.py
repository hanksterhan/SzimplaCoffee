"""Tests for SC-53: merchant registry states and inclusion thresholds."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.db import Base
from szimplacoffee.models import Merchant, MerchantQualityProfile
from szimplacoffee.services.discovery import (
    BUYING_QUALITY_FLOOR,
    BUYING_VIEW_TRUSTED_TIERS,
    CATALOG_VIEW_TIERS,
    CRAWL_TIER_A,
    CRAWL_TIER_B,
    CRAWL_TIER_C,
    CRAWL_TIER_D,
    TRUST_TIER_CANDIDATE,
    TRUST_TIER_REJECTED,
    TRUST_TIER_TRUSTED,
    TRUST_TIER_VERIFIED,
    meets_buying_threshold,
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


def _make_merchant(
    session: Session,
    *,
    name: str = "TestRoast",
    trust_tier: str = TRUST_TIER_CANDIDATE,
    crawl_tier: str = CRAWL_TIER_B,
    is_active: bool = True,
    quality_score: float | None = None,
) -> Merchant:
    m = Merchant(
        name=name,
        canonical_domain=f"{name.lower().replace(' ', '-')}.com",
        homepage_url=f"https://{name.lower().replace(' ', '-')}.com",
        platform_type="shopify",
        crawl_tier=crawl_tier,
        trust_tier=trust_tier,
        is_active=is_active,
    )
    session.add(m)
    session.flush()
    if quality_score is not None:
        profile = MerchantQualityProfile(
            merchant_id=m.id,
            overall_quality_score=quality_score,
            freshness_transparency_score=quality_score,
            shipping_clarity_score=quality_score,
            metadata_quality_score=quality_score,
            espresso_relevance_score=quality_score,
            service_confidence_score=quality_score,
        )
        session.add(profile)
        session.flush()
    return m


# ---------------------------------------------------------------------------
# Registry constant definitions
# ---------------------------------------------------------------------------

def test_trust_tier_constants_defined():
    assert TRUST_TIER_TRUSTED == "trusted"
    assert TRUST_TIER_VERIFIED == "verified"
    assert TRUST_TIER_CANDIDATE == "candidate"
    assert TRUST_TIER_REJECTED == "rejected"


def test_crawl_tier_constants_defined():
    assert CRAWL_TIER_A == "A"
    assert CRAWL_TIER_B == "B"
    assert CRAWL_TIER_C == "C"
    assert CRAWL_TIER_D == "D"


def test_buying_view_trusted_tiers_excludes_candidate():
    assert TRUST_TIER_CANDIDATE not in BUYING_VIEW_TRUSTED_TIERS
    assert TRUST_TIER_TRUSTED in BUYING_VIEW_TRUSTED_TIERS
    assert TRUST_TIER_VERIFIED in BUYING_VIEW_TRUSTED_TIERS


def test_catalog_view_includes_candidate():
    assert TRUST_TIER_CANDIDATE in CATALOG_VIEW_TIERS
    assert TRUST_TIER_TRUSTED in CATALOG_VIEW_TIERS


# ---------------------------------------------------------------------------
# meets_buying_threshold
# ---------------------------------------------------------------------------

def test_trusted_merchant_with_good_quality_is_eligible(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_TRUSTED, crawl_tier=CRAWL_TIER_A, quality_score=0.8)
    assert meets_buying_threshold(m) is True


def test_verified_merchant_with_good_quality_is_eligible(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_VERIFIED, crawl_tier=CRAWL_TIER_B, quality_score=0.7)
    assert meets_buying_threshold(m) is True


def test_candidate_merchant_above_floor_is_eligible(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_CANDIDATE, crawl_tier=CRAWL_TIER_B, quality_score=0.6)
    assert meets_buying_threshold(m) is True


def test_rejected_merchant_is_excluded(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_REJECTED, crawl_tier=CRAWL_TIER_B)
    assert meets_buying_threshold(m) is False


def test_tier_d_merchant_is_excluded(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_TRUSTED, crawl_tier=CRAWL_TIER_D)
    assert meets_buying_threshold(m) is False


def test_inactive_merchant_is_excluded(db_session: Session):
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_TRUSTED, crawl_tier=CRAWL_TIER_A, is_active=False)
    assert meets_buying_threshold(m) is False


def test_merchant_below_quality_floor_is_excluded(db_session: Session):
    below_floor = BUYING_QUALITY_FLOOR - 0.01
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_CANDIDATE, crawl_tier=CRAWL_TIER_B, quality_score=below_floor)
    assert meets_buying_threshold(m) is False


def test_merchant_without_quality_profile_is_optimistically_eligible(db_session: Session):
    """New merchants with no quality profile yet should be allowed in recommendations."""
    m = _make_merchant(db_session, trust_tier=TRUST_TIER_CANDIDATE, crawl_tier=CRAWL_TIER_B, quality_score=None)
    assert meets_buying_threshold(m) is True
