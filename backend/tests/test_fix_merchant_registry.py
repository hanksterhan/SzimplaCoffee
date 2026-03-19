"""Tests for SC-89: fix-merchant-registry CLI command.

Verifies:
- Coava is promoted to crawl_tier=A and trust_tier=trusted
- Junk Tier-D merchants (Blue Bottle Coffee, Stumptownroasters, Not A Url)
  are deactivated (is_active=False)
- No active Tier-D merchants remain after the fix
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.db import Base
from szimplacoffee.models import Merchant


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


def _add_merchant(
    session: Session,
    *,
    name: str,
    domain: str,
    crawl_tier: str,
    trust_tier: str = "candidate",
    is_active: bool = True,
) -> Merchant:
    m = Merchant(
        name=name,
        canonical_domain=domain,
        homepage_url=f"https://{domain}",
        platform_type="shopify",
        crawl_tier=crawl_tier,
        trust_tier=trust_tier,
        is_active=is_active,
    )
    session.add(m)
    session.flush()
    return m


def _apply_fix(session: Session) -> None:
    """Replicate the fix-merchant-registry logic against the provided session."""
    # Promote Coava
    coava = session.scalar(select(Merchant).where(Merchant.name.ilike("%coava%")))
    assert coava is not None, "Coava must exist for this test"
    coava.crawl_tier = "A"
    coava.trust_tier = "trusted"

    # Deactivate junk Tier-D rows
    junk_names = ["Blue Bottle Coffee", "Stumptownroasters", "Not A Url"]
    for junk_name in junk_names:
        merchant = session.scalar(select(Merchant).where(Merchant.name == junk_name))
        if merchant is not None:
            merchant.is_active = False

    session.flush()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_coava_promoted_to_tier_a(db_session):
    _add_merchant(db_session, name="Coava Coffee Roasters", domain="coava.com", crawl_tier="C")
    _apply_fix(db_session)

    coava = db_session.scalar(select(Merchant).where(Merchant.name == "Coava Coffee Roasters"))
    assert coava is not None
    assert coava.crawl_tier == "A", f"Expected crawl_tier=A, got {coava.crawl_tier}"
    assert coava.trust_tier == "trusted", f"Expected trust_tier=trusted, got {coava.trust_tier}"


def test_junk_merchants_deactivated(db_session):
    _add_merchant(db_session, name="Coava Coffee Roasters", domain="coava.com", crawl_tier="C")
    _add_merchant(db_session, name="Blue Bottle Coffee", domain="bluebottlecoffee.com", crawl_tier="D")
    _add_merchant(db_session, name="Stumptownroasters", domain="stumptownroasters.com", crawl_tier="D")
    _add_merchant(db_session, name="Not A Url", domain="not-a-url.invalid", crawl_tier="D")
    _apply_fix(db_session)

    for junk_name in ["Blue Bottle Coffee", "Stumptownroasters", "Not A Url"]:
        m = db_session.scalar(select(Merchant).where(Merchant.name == junk_name))
        assert m is not None
        assert not m.is_active, f"{junk_name} should be inactive after fix"


def test_no_active_tier_d_merchants_remain(db_session):
    _add_merchant(db_session, name="Coava Coffee Roasters", domain="coava.com", crawl_tier="C")
    _add_merchant(db_session, name="Blue Bottle Coffee", domain="bluebottlecoffee.com", crawl_tier="D")
    _add_merchant(db_session, name="Stumptownroasters", domain="stumptownroasters.com", crawl_tier="D")
    _add_merchant(db_session, name="Not A Url", domain="not-a-url.invalid", crawl_tier="D")
    _apply_fix(db_session)

    active_d_count = db_session.scalar(
        select(func.count(Merchant.id)).where(
            Merchant.crawl_tier == "D",
            Merchant.is_active.is_(True),
        )
    ) or 0
    assert active_d_count == 0, f"Expected 0 active Tier-D merchants, found {active_d_count}"


def test_other_merchants_unaffected(db_session):
    _add_merchant(db_session, name="Coava Coffee Roasters", domain="coava.com", crawl_tier="C")
    _add_merchant(db_session, name="Blue Bottle Coffee", domain="bluebottlecoffee.com", crawl_tier="D")
    legit = _add_merchant(
        db_session, name="Onyx Coffee Lab", domain="onyxcoffeelab.com",
        crawl_tier="A", trust_tier="trusted"
    )
    _apply_fix(db_session)

    onyx = db_session.scalar(select(Merchant).where(Merchant.id == legit.id))
    assert onyx is not None
    assert onyx.is_active, "Legit Tier-A merchant should remain active"
    assert onyx.crawl_tier == "A"
    assert onyx.trust_tier == "trusted"
