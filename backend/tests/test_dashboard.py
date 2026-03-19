"""Tests for SC-88 (metadata fill rates) and SC-90 (goal status) dashboard API fields."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.api.dashboard import router as dashboard_router
from szimplacoffee.db import Base, get_session
from szimplacoffee.models import BrewFeedback, Merchant, Product, PurchaseHistory, RecommendationRun
from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture()
def client(engine):
    app = FastAPI()
    app.include_router(dashboard_router, prefix="/api/v1")

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_counter = 0


def _make_merchant(db: Session, name: str, trust_tier: str = "trusted", is_active: bool = True) -> Merchant:
    global _counter
    _counter += 1
    m = Merchant(
        name=name,
        canonical_domain=f"{name}-{_counter}.example.com",
        homepage_url=f"https://{name}-{_counter}.example.com",
        trust_tier=trust_tier,
        is_active=is_active,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _make_product(db: Session, merchant: Merchant, *, origin: str | None = None,
                  process: str | None = None, roast: str | None = None, variety: str | None = None) -> Product:
    global _counter
    _counter += 1
    p = Product(
        merchant_id=merchant.id,
        external_product_id=f"test-product-{_counter}",
        name=f"Test Coffee {_counter}",
        product_url=f"https://example.com/product/{_counter}",
        origin_country=origin,
        process_family=process or "unknown",
        roast_level=roast or "unknown",
        variety_text=variety if variety is not None else "",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ---------------------------------------------------------------------------
# SC-90: goal_status in dashboard response
# ---------------------------------------------------------------------------

class TestGoalStatus:
    def test_goal_status_present_in_response(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "goal_status" in data
        gs = data["goal_status"]
        # All 8 required fields
        for field in [
            "merchants_15_plus", "metadata_70pct", "recs_produce_results",
            "today_works", "purchases_10_plus", "brew_feedback_3_plus",
            "ui_works", "tests_pass", "all_complete",
        ]:
            assert field in gs, f"Missing goal_status field: {field}"

    def test_all_false_on_empty_db(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["merchants_15_plus"] is False
        assert gs["metadata_70pct"] is False
        assert gs["recs_produce_results"] is False
        assert gs["purchases_10_plus"] is False
        assert gs["brew_feedback_3_plus"] is False
        assert gs["all_complete"] is False

    def test_ui_works_and_tests_pass_default_true(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["ui_works"] is True
        assert gs["tests_pass"] is True

    def test_merchants_15_plus_true_when_15_trusted(self, client, db):
        for i in range(15):
            _make_merchant(db, f"merchant{i}", trust_tier="trusted")
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["merchants_15_plus"] is True

    def test_merchants_15_plus_false_when_14_trusted(self, client, db):
        for i in range(14):
            _make_merchant(db, f"merchant{i}", trust_tier="trusted")
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["merchants_15_plus"] is False

    def test_merchants_15_plus_ignores_inactive(self, client, db):
        for i in range(15):
            _make_merchant(db, f"active{i}", trust_tier="trusted", is_active=True)
        # Add inactive ones — should not count
        for i in range(5):
            _make_merchant(db, f"inactive{i}", trust_tier="trusted", is_active=False)
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["merchants_15_plus"] is True

    def test_merchants_15_plus_ignores_candidate_tier(self, client, db):
        # 20 candidate merchants should not satisfy the criterion
        for i in range(20):
            _make_merchant(db, f"cand{i}", trust_tier="candidate")
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["merchants_15_plus"] is False

    def test_purchases_10_plus_true_when_10_records(self, client, db):
        m = _make_merchant(db, "merchant-a")
        for _ in range(10):
            ph = PurchaseHistory(
                merchant_id=m.id,
                product_name="Test Bag",
                price_cents=2000,
                weight_grams=340,
            )
            db.add(ph)
        db.commit()
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["purchases_10_plus"] is True

    def test_brew_feedback_3_plus_true_when_3_records(self, client, db):
        for _ in range(3):
            bf = BrewFeedback(shot_style="18g modern", rating=4.0)
            db.add(bf)
        db.commit()
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["brew_feedback_3_plus"] is True

    def test_recs_produce_results_true_when_run_exists(self, client, db):
        rr = RecommendationRun(request_json="{}", top_result_json="{}")
        db.add(rr)
        db.commit()
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["recs_produce_results"] is True

    def test_recs_produce_results_false_on_empty_db(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["recs_produce_results"] is False

    def test_today_works_mirrors_recs_produce_results(self, client, db):
        rr = RecommendationRun(request_json="{}", top_result_json="{}")
        db.add(rr)
        db.commit()
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["today_works"] == gs["recs_produce_results"]

    def test_all_complete_false_when_any_criterion_false(self, client, db):
        # merchants ok but nothing else
        for i in range(15):
            _make_merchant(db, f"m{i}")
        r = client.get("/api/v1/dashboard/metrics")
        gs = r.json()["goal_status"]
        assert gs["all_complete"] is False


# ---------------------------------------------------------------------------
# SC-88: metadata_fill_rates in dashboard response
# ---------------------------------------------------------------------------

class TestMetadataFillRates:
    def test_metadata_fill_rates_present(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "metadata_fill_rates" in data
        mfr = data["metadata_fill_rates"]
        for field in ["origin_pct", "process_pct", "roast_pct", "variety_pct"]:
            assert field in mfr

    def test_all_zero_on_empty_db(self, client):
        r = client.get("/api/v1/dashboard/metrics")
        mfr = r.json()["metadata_fill_rates"]
        assert mfr["origin_pct"] == 0
        assert mfr["process_pct"] == 0
        assert mfr["roast_pct"] == 0
        assert mfr["variety_pct"] == 0

    def test_origin_pct_100_when_all_products_have_origin(self, client, db):
        m = _make_merchant(db, "roaster-x")
        for _ in range(4):
            _make_product(db, m, origin="Ethiopia")
        r = client.get("/api/v1/dashboard/metrics")
        mfr = r.json()["metadata_fill_rates"]
        assert mfr["origin_pct"] == 100

    def test_origin_pct_50_when_half_have_origin(self, client, db):
        m = _make_merchant(db, "roaster-y")
        for _ in range(2):
            _make_product(db, m, origin="Ethiopia")
        for _ in range(2):
            _make_product(db, m, origin=None)
        r = client.get("/api/v1/dashboard/metrics")
        mfr = r.json()["metadata_fill_rates"]
        assert mfr["origin_pct"] == 50

    def test_process_pct_excludes_unknown(self, client, db):
        m = _make_merchant(db, "roaster-z")
        _make_product(db, m, process="washed")
        _make_product(db, m, process="unknown")
        r = client.get("/api/v1/dashboard/metrics")
        mfr = r.json()["metadata_fill_rates"]
        assert mfr["process_pct"] == 50

    def test_variety_pct_counts_nonempty_strings(self, client, db):
        m = _make_merchant(db, "roaster-v")
        _make_product(db, m, variety="Gesha")
        _make_product(db, m, variety="")
        _make_product(db, m, variety=None)
        r = client.get("/api/v1/dashboard/metrics")
        mfr = r.json()["metadata_fill_rates"]
        # 1/3 = 33%
        assert mfr["variety_pct"] == 33
