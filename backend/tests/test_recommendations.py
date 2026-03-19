from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.api.recommendations import router as recommendations_router
from szimplacoffee.db import Base, get_session
from szimplacoffee.services.discovery import _decode_bing_result_url
from szimplacoffee.models import (
    BrewFeedback,
    Merchant,
    MerchantPersonalProfile,
    MerchantPromo,
    MerchantQualityProfile,
    OfferSnapshot,
    Product,
    ProductVariant,
    VariantDealFact,
)
from szimplacoffee.services.recommendations import (
    BREW_PENALTY_WEIGHT,
    RecommendationRequest,
    _build_pros,
    _discounted_price_cents,
    _espresso_fit,
    build_biggest_sales,
    build_recommendations,
    build_wait_assessment,
    materialize_variant_deal_facts,
    _price_per_oz_cents,
    _quantity_score,
)
from szimplacoffee.services.crawlers import (
    _extract_code,
    _is_coffee_product,
    _normalize_product_name,
    _normalize_promo_key,
    _normalize_single_origin_flag,
    _shopify_catalog_urls,
)
from szimplacoffee.services.platforms import normalize_url, recommended_crawl_tier


def test_quantity_score_prefers_small_bags_for_small_mode() -> None:
    small = _quantity_score(340, "12-18 oz", False)
    bulk = _quantity_score(907, "12-18 oz", False)
    assert small > bulk


def test_request_dataclass_builds() -> None:
    request = RecommendationRequest(
        shot_style="turbo",
        quantity_mode="12-18 oz",
        bulk_allowed=False,
    )
    assert request.shot_style == "turbo"


def test_decode_bing_result_url_extracts_target() -> None:
    href = (
        "https://www.bing.com/ck/a?!&&p=abc"
        "&u=a1aHR0cHM6Ly9vbnl4Y29mZmVlbGFiLmNvbS8"
        "&ntb=1"
    )
    assert _decode_bing_result_url(href) == "https://onyxcoffeelab.com/"


def test_non_coffee_products_are_filtered() -> None:
    assert not _is_coffee_product("Breville Bambino Plus Espresso Machine", "Equipment")
    assert _is_coffee_product("Ethiopia Bochesa", "Coffee")


def test_single_origin_flag_rejects_blends() -> None:
    assert not _normalize_single_origin_flag("20th Anniversary Blend", ["single origin"], "single origin celebration coffee")
    assert _normalize_single_origin_flag("Ethiopia Bochesa", ["single origin"], "washed single origin coffee")


def test_subscription_downranks_espresso_fit() -> None:
    class ProductStub:
        process_text = "Washed"
        tasting_notes_text = "Citrus"
        name = "Single Origin Subscription"
        is_espresso_recommended = False

    score, reasons = _espresso_fit(ProductStub(), "modern_58mm")
    assert score < 0.65
    assert any("subscription" in reason for reason in reasons)


def test_price_per_oz_cents_uses_current_recommendation_helper() -> None:
    assert _price_per_oz_cents(2400, 340) == 200
    assert _price_per_oz_cents(2400, None) is None


def test_extract_code_requires_real_promo_code_shape() -> None:
    assert _extract_code("Use code SAVE10 for espresso bags") == "SAVE10"
    assert _extract_code("Read the code that governs use of this website") is None


def test_promo_key_dedupes_shipping_variants() -> None:
    key_one = _normalize_promo_key("free_shipping_variant", 800, None, "2lb [Ships free] includes free shipping")
    key_two = _normalize_promo_key("free_shipping_variant", 800, None, "5lb [Ships free] includes free shipping")
    assert key_one == key_two


def test_recommended_crawl_tier_prefers_machine_readable_platforms() -> None:
    assert recommended_crawl_tier("shopify", 0.95) == "A"
    assert recommended_crawl_tier("squarespace", 0.82) == "B"
    assert recommended_crawl_tier("custom", 0.72) == "C"
    assert recommended_crawl_tier("unknown", 0.3) == "D"


def test_normalize_product_name_replaces_html_breaks() -> None:
    assert _normalize_product_name("Colombia <BR>La Despensa") == "Colombia • La Despensa"


def test_normalize_url_strips_query_and_fragment() -> None:
    assert normalize_url("https://us.lacabra.com/collections/coffee?showBanner=false#top") == "https://us.lacabra.com/collections/coffee"


def test_shopify_catalog_urls_prefer_collection_endpoint() -> None:
    urls = _shopify_catalog_urls("https://us.lacabra.com/collections/coffee?showBanner=false")
    assert urls[0] == "https://us.lacabra.com/collections/coffee/products.json?limit=250"
    assert urls[1] == "https://us.lacabra.com/products.json?limit=250"


def test_discounted_price_cents_applies_percent_promo() -> None:
    offer = OfferSnapshot(price_cents=4000, compare_at_price_cents=None, subscription_price_cents=None, is_on_sale=False, is_available=True, source_url="https://example.com")
    promo = MerchantPromo(
        promo_key="save10",
        promo_type="percent_off",
        title="Save 10%",
        details="",
        code="SAVE10",
        estimated_value_cents=1000,
        source_urls="https://example.com",
        confidence=0.9,
        is_active=True,
    )
    discounted, label = _discounted_price_cents(4800, offer, promo)
    assert discounted == 4320
    assert label == "10% off"


def test_build_pros_emits_buyer_facing_summary() -> None:
    pros = _build_pros(
        merchant_score=0.85,
        quantity_score=1.0,
        deal_score=0.82,
        espresso_reasons=["merchant signals espresso suitability"],
        deal_reasons=["qualifies for free shipping"],
        history_reasons=["matches a merchant with strong purchase history"],
        promo_label="10% off",
    )
    assert "Trusted merchant with a strong quality signal" in pros
    assert "Bag size matches your current buying window" in pros
    assert "Strong delivered value for the amount of coffee" in pros
    assert len(pros) == 4


def _seed_offer(session: Session, variant: ProductVariant, *, observed_at: datetime, price_cents: int, compare_at_price_cents: int | None = None) -> None:
    session.add(
        OfferSnapshot(
            variant_id=variant.id,
            observed_at=observed_at,
            price_cents=price_cents,
            compare_at_price_cents=compare_at_price_cents,
            subscription_price_cents=None,
            is_on_sale=bool(compare_at_price_cents and compare_at_price_cents > price_cents),
            is_available=True,
            source_url="https://example.com/product",
        )
    )


@pytest.fixture()
def deal_test_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    now = datetime.now(UTC)

    with Session(engine) as session:
        merchant = Merchant(
            name="Alpha Coffee",
            canonical_domain="alpha.example",
            homepage_url="https://alpha.example",
            platform_type="shopify",
        )
        session.add(merchant)
        session.flush()
        session.add(
            MerchantQualityProfile(
                merchant_id=merchant.id,
                overall_quality_score=0.9,
                freshness_transparency_score=0.88,
                metadata_quality_score=0.86,
            )
        )
        session.add(
            MerchantPersonalProfile(
                merchant_id=merchant.id,
                personal_trust_score=0.84,
                would_reorder=True,
            )
        )
        session.add(
            MerchantPromo(
                merchant_id=merchant.id,
                promo_key="sale10",
                promo_type="percent_off",
                title="Save 10%",
                details="Spring sale",
                code="SALE10",
                estimated_value_cents=1000,
                source_urls="https://alpha.example",
                confidence=0.9,
                is_active=True,
            )
        )

        product = Product(
            merchant_id=merchant.id,
            external_product_id="wash-1",
            name="Washed Colombia",
            product_url="https://alpha.example/products/washed-colombia",
            image_url="",
            origin_text="Colombia",
            origin_country="Colombia",
            process_text="Washed",
            process_family="washed",
            roast_cues="medium-dark",
            roast_level="medium-dark",
            tasting_notes_text="citrus, caramel",
            metadata_confidence=0.9,
            metadata_source="parser",
            product_category="coffee",
            is_single_origin=True,
            is_espresso_recommended=True,
            is_active=True,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(product)
        session.flush()

        variant = ProductVariant(
            product_id=product.id,
            external_variant_id="wash-1-12oz",
            label="12 oz",
            weight_grams=340,
            is_whole_bean=True,
            is_available=True,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(variant)
        session.flush()

        _seed_offer(session, variant, observed_at=now, price_cents=1800, compare_at_price_cents=2400)
        _seed_offer(session, variant, observed_at=now - timedelta(days=3), price_cents=2400)
        _seed_offer(session, variant, observed_at=now - timedelta(days=10), price_cents=2600)
        _seed_offer(session, variant, observed_at=now - timedelta(days=20), price_cents=2800)

        second_product = Product(
            merchant_id=merchant.id,
            external_product_id="blend-1",
            name="Daily Blend",
            product_url="https://alpha.example/products/daily-blend",
            image_url="",
            origin_text="Brazil",
            origin_country="Brazil",
            process_text="Natural",
            process_family="natural",
            roast_cues="medium",
            roast_level="medium",
            tasting_notes_text="chocolate",
            metadata_confidence=0.8,
            metadata_source="parser",
            product_category="coffee",
            is_single_origin=False,
            is_espresso_recommended=True,
            is_active=True,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(second_product)
        session.flush()

        second_variant = ProductVariant(
            product_id=second_product.id,
            external_variant_id="blend-1-12oz",
            label="12 oz",
            weight_grams=340,
            is_whole_bean=True,
            is_available=True,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(second_variant)
        session.flush()

        _seed_offer(session, second_variant, observed_at=now, price_cents=2200)
        _seed_offer(session, second_variant, observed_at=now - timedelta(days=3), price_cents=2200)
        _seed_offer(session, second_variant, observed_at=now - timedelta(days=10), price_cents=2250)
        session.commit()

        seeded = {
            "merchant_id": merchant.id,
            "product_id": product.id,
            "product_name": product.name,
            "second_product_id": second_product.id,
            "second_product_name": second_product.name,
            "variant_id": variant.id,
        }

    app = FastAPI()
    app.include_router(recommendations_router, prefix="/api/v1")

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client, engine, seeded

    app.dependency_overrides.clear()


def test_materialize_variant_deal_facts_uses_offer_history(deal_test_client) -> None:
    _client, engine, seeded = deal_test_client

    with Session(engine) as session:
        facts = materialize_variant_deal_facts(session)
        fact = facts[seeded["variant_id"]]

        assert fact.offer_count == 4
        assert fact.baseline_7d_cents == 2400
        assert fact.baseline_30d_cents == 2600
        assert fact.historical_low_cents == 1800
        assert fact.historical_high_cents == 2800
        assert fact.compare_at_discount_percent == 25.0
        assert fact.price_drop_7d_percent > 0
        assert fact.price_drop_30d_percent > 0
        assert session.scalar(select(VariantDealFact).where(VariantDealFact.variant_id == seeded["variant_id"])) is not None


def test_build_biggest_sales_uses_history_promo_and_price_per_oz_context(deal_test_client) -> None:
    _client, engine, seeded = deal_test_client

    with Session(engine) as session:
        candidates = build_biggest_sales(session, limit=5)

    assert candidates
    top = candidates[0]
    assert top.product_name == seeded["product_name"]
    assert top.best_promo_label == "10% off"
    assert top.price_drop_7d_percent > 0
    assert top.price_drop_30d_percent > 0
    assert any("7-day median" in reason for reason in top.reasons)
    assert any("catalog baseline" in reason for reason in top.reasons)


def test_biggest_sales_endpoint_returns_explainable_candidates(deal_test_client) -> None:
    client, _engine, seeded = deal_test_client

    response = client.get("/api/v1/recommendations/biggest-sales", params={"limit": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["product_name"] == seeded["product_name"]
    assert payload[0]["best_promo_label"] == "10% off"
    assert payload[0]["score"] > 0.58
    assert payload[0]["reasons"]


# SC-66: Regression tests — build_recommendations returns results with seeded data
def test_build_recommendations_returns_candidate_with_seeded_offer_snapshot(deal_test_client) -> None:
    """Guard the full recommendation pipeline: seeded offer_snapshot must produce >= 1 candidate."""
    _client, engine, seeded = deal_test_client

    with Session(engine) as session:
        request = RecommendationRequest(
            shot_style="modern_58mm",
            quantity_mode="12-18 oz",
            bulk_allowed=False,
            current_inventory_grams=0,
        )
        results, _filtered = build_recommendations(session, request)

    assert len(results) >= 1, (
        "Expected at least 1 recommendation candidate but got none. "
        "Check meets_buying_threshold, offer_snapshot presence, and VariantDealFact materialization."
    )
    scores = [r.score for r in results]
    assert all(s > 0 for s in scores), f"All scores must be positive, got: {scores}"


def test_recommendations_endpoint_returns_ranked_results_with_seeded_data(deal_test_client) -> None:
    """SC-66 AC-1: POST /api/v1/recommendations returns >= 1 ranked result when offer_snapshots exist."""
    client, _engine, _seeded = deal_test_client

    response = client.post(
        "/api/v1/recommendations",
        json={"current_inventory_grams": 0},
    )

    assert response.status_code in (200, 201)
    payload = response.json()
    # API returns {top_result, alternatives, ...} shape
    top_result = payload.get("top_result")
    alternatives = payload.get("alternatives", [])
    all_results = ([top_result] if top_result else []) + alternatives
    assert len(all_results) >= 1, (
        f"Expected >= 1 recommendation but got 0. Full response: {payload}"
    )
    assert all_results[0]["score"] > 0


def test_wait_is_false_when_inventory_is_zero(deal_test_client) -> None:
    """SC-66: wait_recommendation must be False when current_inventory_grams=0."""
    _client, engine, _seeded = deal_test_client

    with Session(engine) as session:
        request = RecommendationRequest(
            shot_style="modern_58mm",
            quantity_mode="12-18 oz",
            bulk_allowed=False,
            current_inventory_grams=0,
        )
        candidates, _ = build_recommendations(session, request)

    wait, rationale = build_wait_assessment(
        candidates,
        no_candidates=len(candidates) == 0,
        current_inventory_grams=0,
    )

    assert not wait, f"Expected wait=False with 0g inventory but got wait=True. Rationale: {rationale}"


def _scores_by_product_name(engine) -> dict[str, float]:
    with Session(engine) as session:
        request = RecommendationRequest(
            shot_style="modern_58mm",
            quantity_mode="12-18 oz",
            bulk_allowed=False,
            current_inventory_grams=0,
        )
        results, _ = build_recommendations(session, request)
    return {candidate.product_name: candidate.score for candidate in results}


# SC-72: brew feedback penalty tests

def test_brew_feedback_penalty_does_not_affect_products_without_feedback(deal_test_client) -> None:
    _client, engine, seeded = deal_test_client
    baseline_scores = _scores_by_product_name(engine)

    with Session(engine) as session:
        session.add(
            BrewFeedback(
                product_id=seeded["second_product_id"],
                shot_style="modern_58mm",
                rating=2.0,
                would_rebuy=False,
            )
        )
        session.commit()

    updated_scores = _scores_by_product_name(engine)

    assert updated_scores[seeded["product_name"]] == baseline_scores[seeded["product_name"]]


def test_brew_feedback_penalty_skips_products_at_or_above_threshold(deal_test_client) -> None:
    _client, engine, seeded = deal_test_client
    baseline_scores = _scores_by_product_name(engine)

    with Session(engine) as session:
        session.add(
            BrewFeedback(
                product_id=seeded["product_id"],
                shot_style="modern_58mm",
                rating=4.0,
                would_rebuy=True,
            )
        )
        session.commit()

    updated_scores = _scores_by_product_name(engine)

    assert updated_scores[seeded["product_name"]] == baseline_scores[seeded["product_name"]]


def test_brew_feedback_penalty_downranks_products_below_threshold(deal_test_client) -> None:
    _client, engine, seeded = deal_test_client
    baseline_scores = _scores_by_product_name(engine)

    with Session(engine) as session:
        session.add_all(
            [
                BrewFeedback(
                    product_id=seeded["product_id"],
                    shot_style="modern_58mm",
                    rating=2.0,
                    would_rebuy=False,
                ),
                BrewFeedback(
                    product_id=seeded["product_id"],
                    shot_style="modern_58mm",
                    rating=2.0,
                    would_rebuy=False,
                ),
            ]
        )
        session.commit()

    updated_scores = _scores_by_product_name(engine)

    assert updated_scores[seeded["product_name"]] == pytest.approx(
        baseline_scores[seeded["product_name"]] - BREW_PENALTY_WEIGHT
    )


# SC-67: explain_scores tests
def test_explain_scores_true_returns_score_breakdown(deal_test_client) -> None:
    """SC-67 AC-1: explain_scores=True must return score_breakdown per candidate."""
    _client, engine, _seeded = deal_test_client

    with Session(engine) as session:
        request = RecommendationRequest(
            shot_style="modern_58mm",
            quantity_mode="12-18 oz",
            bulk_allowed=False,
            current_inventory_grams=0,
            explain_scores=True,
        )
        results, filtered = build_recommendations(session, request)

    assert len(results) >= 1, "Expected at least 1 candidate with explain_scores=True"
    for candidate in results:
        assert candidate.score_breakdown is not None, (
            f"Expected score_breakdown on {candidate.product_name} but got None"
        )
        breakdown = candidate.score_breakdown
        for field in ("merchant_score", "quantity_score", "espresso_score", "deal_score", "freshness_score", "history_score", "promo_bonus", "total"):
            assert field in breakdown, f"Missing field '{field}' in score_breakdown"
        assert breakdown["total"] == candidate.score, (
            f"score_breakdown.total={breakdown['total']} must match candidate.score={candidate.score}"
        )
    # filtered list is populated
    assert isinstance(filtered, list)


def test_explain_scores_false_no_score_breakdown(deal_test_client) -> None:
    """SC-67 AC-2: explain_scores=False (default) must not populate score_breakdown."""
    _client, engine, _seeded = deal_test_client

    with Session(engine) as session:
        request = RecommendationRequest(
            shot_style="modern_58mm",
            quantity_mode="12-18 oz",
            bulk_allowed=False,
            current_inventory_grams=0,
            explain_scores=False,
        )
        results, filtered = build_recommendations(session, request)

    assert len(results) >= 1
    for candidate in results:
        assert candidate.score_breakdown is None, (
            f"Expected score_breakdown=None when explain_scores=False on {candidate.product_name}"
        )
    assert filtered == [], "filtered_candidates must be empty when explain_scores=False"


def test_explain_scores_api_endpoint(deal_test_client) -> None:
    """SC-67: POST /api/v1/recommendations with explain_scores=True returns score_breakdown and filtered_candidates."""
    client, _engine, _seeded = deal_test_client

    response = client.post(
        "/api/v1/recommendations",
        json={"current_inventory_grams": 0, "explain_scores": True},
    )

    assert response.status_code in (200, 201)
    payload = response.json()

    top_result = payload.get("top_result")
    assert top_result is not None, "Expected top_result with explain_scores=True and seeded data"
    assert "score_breakdown" in top_result, "top_result must include score_breakdown when explain_scores=True"
    assert top_result["score_breakdown"] is not None

    assert "filtered_candidates" in payload, "Response must include filtered_candidates key"
    assert payload["filtered_candidates"] is not None
    assert isinstance(payload["filtered_candidates"], list)
