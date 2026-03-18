"""Tests for purchase history and brew feedback API endpoints.

Covers:
- POST /api/v1/purchases creates and persists purchase (SC-69 fix: commit on write)
- GET /api/v1/purchases returns all purchases
- GET /api/v1/purchases/stats returns aggregate stats
- GET /api/v1/purchases/{id} returns single purchase
- PUT /api/v1/purchases/{id} updates purchase and persists
- DELETE /api/v1/purchases/{id} removes purchase
- POST /api/v1/purchases/{id}/feedback creates brew feedback
- GET /api/v1/purchases/{id}/feedback lists brew feedback
- PUT /api/v1/feedback/{id} updates feedback
- DELETE /api/v1/feedback/{id} removes feedback
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from szimplacoffee.db import SessionLocal, engine
from szimplacoffee.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_purchases():
    """Remove test purchases before and after each test."""
    with SessionLocal() as db:
        db.execute(text("DELETE FROM brew_feedback WHERE purchase_id IN (SELECT id FROM purchase_history WHERE source_ref = 'test')"))
        db.execute(text("DELETE FROM purchase_history WHERE source_ref = 'test'"))
        db.commit()
    yield
    with SessionLocal() as db:
        db.execute(text("DELETE FROM brew_feedback WHERE purchase_id IN (SELECT id FROM purchase_history WHERE source_ref = 'test')"))
        db.execute(text("DELETE FROM purchase_history WHERE source_ref = 'test'"))
        db.commit()


@pytest.fixture()
def merchant_id():
    """Return a valid merchant ID (first active merchant)."""
    with SessionLocal() as db:
        m = db.execute(text("SELECT id FROM merchants LIMIT 1")).fetchone()
        if m is None:
            # Create a minimal test merchant
            result = db.execute(
                text("INSERT INTO merchants (name, domain, is_active, crawl_tier) VALUES ('Test Roaster', 'testr.com', 1, 'B') RETURNING id")
            )
            db.commit()
            return result.fetchone()[0]
        return m[0]


def _make_purchase(client, merchant_id: int, name: str = "Test Ethiopia Natural") -> dict:
    resp = client.post("/api/v1/purchases", json={
        "merchant_id": merchant_id,
        "product_name": name,
        "origin_text": "Ethiopia",
        "process_text": "Natural",
        "price_cents": 1800,
        "weight_grams": 340,
        "source_system": "manual",
        "source_ref": "test",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Purchase CRUD ─────────────────────────────────────────────────────────────

class TestCreatePurchase:
    def test_create_returns_201(self, client, merchant_id):
        resp = client.post("/api/v1/purchases", json={
            "merchant_id": merchant_id,
            "product_name": "Kenya Kiambu AA",
            "origin_text": "Kenya",
            "process_text": "Washed",
            "price_cents": 2200,
            "weight_grams": 340,
            "source_system": "manual",
            "source_ref": "test",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["product_name"] == "Kenya Kiambu AA"
        assert data["id"] > 0

    def test_create_persists_to_db(self, client, merchant_id):
        """Core SC-69 regression: writes must survive to DB (commit fix)."""
        data = _make_purchase(client, merchant_id, "Persist Test")
        purchase_id = data["id"]

        # Verify DB directly
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT product_name FROM purchase_history WHERE id = :id"),
                {"id": purchase_id},
            ).fetchone()
        assert row is not None, "Purchase was not persisted to DB (missing commit)"
        assert row[0] == "Persist Test"

    def test_create_with_unknown_merchant_returns_404(self, client):
        resp = client.post("/api/v1/purchases", json={
            "merchant_id": 999999,
            "product_name": "Ghost",
            "price_cents": 100,
            "weight_grams": 340,
            "source_system": "manual",
            "source_ref": "test",
        })
        assert resp.status_code == 404

    def test_get_list_includes_new_purchase(self, client, merchant_id):
        _make_purchase(client, merchant_id, "List Inclusion Test")
        resp = client.get("/api/v1/purchases")
        assert resp.status_code == 200
        names = [p["product_name"] for p in resp.json()]
        assert "List Inclusion Test" in names

    def test_get_by_id(self, client, merchant_id):
        created = _make_purchase(client, merchant_id, "Detail Test")
        resp = client.get(f"/api/v1/purchases/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["product_name"] == "Detail Test"

    def test_get_by_id_not_found(self, client):
        resp = client.get("/api/v1/purchases/999999")
        assert resp.status_code == 404

    def test_update_persists(self, client, merchant_id):
        created = _make_purchase(client, merchant_id, "Update Source")
        resp = client.put(f"/api/v1/purchases/{created['id']}", json={"product_name": "Update Target"})
        assert resp.status_code == 200
        assert resp.json()["product_name"] == "Update Target"

        # Verify DB
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT product_name FROM purchase_history WHERE id = :id"),
                {"id": created["id"]},
            ).fetchone()
        assert row[0] == "Update Target"

    def test_delete_removes_purchase(self, client, merchant_id):
        created = _make_purchase(client, merchant_id, "Delete Me")
        resp = client.delete(f"/api/v1/purchases/{created['id']}")
        assert resp.status_code == 204

        # Verify gone
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM purchase_history WHERE id = :id"),
                {"id": created["id"]},
            ).fetchone()
        assert row is None


class TestPurchaseStats:
    def test_stats_returns_200(self, client):
        resp = client.get("/api/v1/purchases/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_purchases" in data
        assert "total_spent_cents" in data

    def test_stats_counts_new_purchase(self, client, merchant_id):
        before = client.get("/api/v1/purchases/stats").json()["total_purchases"]
        _make_purchase(client, merchant_id)
        after = client.get("/api/v1/purchases/stats").json()["total_purchases"]
        assert after == before + 1


# ── Brew Feedback ─────────────────────────────────────────────────────────────

class TestBrewFeedback:
    def test_create_feedback_persists(self, client, merchant_id):
        purchase = _make_purchase(client, merchant_id)
        pid = purchase["id"]

        resp = client.post(f"/api/v1/purchases/{pid}/feedback", json={
            "shot_style": "58mm modern",
            "grinder": "Timemore Sculptor 078S",
            "basket": "VST 20g",
            "rating": 8.5,
            "would_rebuy": True,
            "difficulty_score": 3.0,
            "notes": "Juicy and bright",
        })
        assert resp.status_code == 201
        fb = resp.json()
        assert fb["rating"] == 8.5
        assert fb["purchase_id"] == pid

        # Verify in DB
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT rating FROM brew_feedback WHERE id = :id"),
                {"id": fb["id"]},
            ).fetchone()
        assert row is not None, "Feedback was not persisted (missing commit)"
        assert row[0] == 8.5

    def test_list_feedback(self, client, merchant_id):
        purchase = _make_purchase(client, merchant_id)
        pid = purchase["id"]
        client.post(f"/api/v1/purchases/{pid}/feedback", json={
            "shot_style": "turbo",
            "rating": 7.0,
        })
        resp = client.get(f"/api/v1/purchases/{pid}/feedback")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_update_feedback_persists(self, client, merchant_id):
        purchase = _make_purchase(client, merchant_id)
        pid = purchase["id"]
        fb = client.post(f"/api/v1/purchases/{pid}/feedback", json={
            "shot_style": "lever",
            "rating": 6.0,
        }).json()

        resp = client.put(f"/api/v1/feedback/{fb['id']}", json={"rating": 9.5})
        assert resp.status_code == 200
        assert resp.json()["rating"] == 9.5

    def test_delete_feedback(self, client, merchant_id):
        purchase = _make_purchase(client, merchant_id)
        pid = purchase["id"]
        fb = client.post(f"/api/v1/purchases/{pid}/feedback", json={
            "shot_style": "lever",
            "rating": 5.0,
        }).json()

        resp = client.delete(f"/api/v1/feedback/{fb['id']}")
        assert resp.status_code == 204

        # Verify gone
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id FROM brew_feedback WHERE id = :id"),
                {"id": fb["id"]},
            ).fetchone()
        assert row is None

    def test_feedback_on_missing_purchase_returns_404(self, client):
        resp = client.post("/api/v1/purchases/999999/feedback", json={
            "shot_style": "turbo",
            "rating": 5.0,
        })
        assert resp.status_code == 404


# ── SC-70: recommendation_run_id linkage ──────────────────────────────────────

class TestPurchaseRecommendationLink:
    """Verify recommendation_run_id is accepted, persisted, and returned."""

    def test_create_without_recommendation_run_id_succeeds(self, client, merchant_id):
        """Existing callers without the field must continue to work."""
        resp = client.post("/api/v1/purchases", json={
            "merchant_id": merchant_id,
            "product_name": "No Run Link",
            "price_cents": 1800,
            "weight_grams": 340,
            "source_system": "manual",
            "source_ref": "test",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data.get("recommendation_run_id") is None

    def test_create_with_null_recommendation_run_id_succeeds(self, client, merchant_id):
        """Explicit null is also fine."""
        resp = client.post("/api/v1/purchases", json={
            "merchant_id": merchant_id,
            "product_name": "Null Run Link",
            "price_cents": 1800,
            "weight_grams": 340,
            "source_system": "manual",
            "source_ref": "test",
            "recommendation_run_id": None,
        })
        assert resp.status_code == 201
        assert resp.json().get("recommendation_run_id") is None

    def test_create_with_recommendation_run_id_persists(self, client, merchant_id):
        """When a valid recommendation_run_id is passed it is stored and returned."""
        # Get or create a recommendation run
        with SessionLocal() as db:
            row = db.execute(text("SELECT id FROM recommendation_runs LIMIT 1")).fetchone()
            if row is None:
                result = db.execute(
                    text(
                        "INSERT INTO recommendation_runs "
                        "(created_at, inventory_grams, status) "
                        "VALUES (datetime('now'), 0, 'completed') RETURNING id"
                    )
                )
                db.commit()
                run_id = result.fetchone()[0]
            else:
                run_id = row[0]

        resp = client.post("/api/v1/purchases", json={
            "merchant_id": merchant_id,
            "product_name": "Run Linked Purchase",
            "price_cents": 2000,
            "weight_grams": 340,
            "source_system": "manual",
            "source_ref": "test",
            "recommendation_run_id": run_id,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["recommendation_run_id"] == run_id

        # Verify DB
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT recommendation_run_id FROM purchase_history WHERE id = :id"),
                {"id": data["id"]},
            ).fetchone()
        assert row is not None
        assert row[0] == run_id

    def test_get_purchase_returns_recommendation_run_id(self, client, merchant_id):
        """GET /api/v1/purchases/{id} response includes recommendation_run_id."""
        created = _make_purchase(client, merchant_id, "Get With Run ID")
        resp = client.get(f"/api/v1/purchases/{created['id']}")
        assert resp.status_code == 200
        assert "recommendation_run_id" in resp.json()

    def test_list_purchases_returns_recommendation_run_id_field(self, client, merchant_id):
        """GET /api/v1/purchases list items include recommendation_run_id."""
        _make_purchase(client, merchant_id, "List Run ID Check")
        resp = client.get("/api/v1/purchases")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) > 0
        assert "recommendation_run_id" in items[0]

    def test_column_exists_in_db(self):
        """AC-1: confirm column is present after migration."""
        with engine.connect() as conn:
            cols = [r[1] for r in conn.execute(text("PRAGMA table_info(purchase_history)")).fetchall()]
        assert "recommendation_run_id" in cols
