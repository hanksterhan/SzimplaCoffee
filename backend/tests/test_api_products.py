from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from szimplacoffee.api.products import (
    _coffee_like_merch_clause,
    _normalize_query_default,
    _parse_categories,
    _parse_csv_ints,
    _parse_csv_values,
    _select_primary_variant,
    _variant_latest_offer,
    router as products_router,
)
from szimplacoffee.db import Base, get_session
from szimplacoffee.models import Merchant, OfferSnapshot, Product, ProductVariant, VariantDealFact


def test_normalize_query_default_unwraps_fastapi_query_objects():
    assert _normalize_query_default(Query(None)) is None
    assert _normalize_query_default(Query("coffee")) == "coffee"


def test_parse_categories_defaults_to_coffee():
    assert _parse_categories(None) == ["coffee"]
    assert _parse_categories("") == ["coffee"]


def test_parse_categories_supports_multi_select_and_dedupes():
    assert _parse_categories("coffee, merch,coffee") == ["coffee", "merch"]


def test_parse_categories_treats_all_as_passthrough():
    assert _parse_categories("coffee,all,merch") == ["all"]


def test_parse_csv_helpers_dedupe_and_ignore_invalid_ints():
    assert _parse_csv_values("washed,natural,washed") == ["washed", "natural"]
    assert _parse_csv_ints("2,3,2,nope") == [2, 3]


def test_coffee_like_merch_clause_has_expected_guardrails():
    clause = str(
        _coffee_like_merch_clause().compile(compile_kwargs={"literal_binds": True})
    ).lower()

    assert "product_category = 'merch'" in clause
    assert "weight_grams >= 340" in clause
    assert "is_whole_bean is true" in clause
    assert "subscription" in clause
    assert "tee" in clause
    assert Product.__tablename__ in clause


def test_variant_latest_offer_falls_back_to_latest_offer_in_offers_list():
    older = SimpleNamespace(observed_at=datetime.now(UTC) - timedelta(days=1), price_cents=2000)
    newer = SimpleNamespace(observed_at=datetime.now(UTC), price_cents=1800)
    variant = SimpleNamespace(offers=[older, newer])

    assert _variant_latest_offer(variant) is newer


def test_select_primary_variant_uses_offer_fallback_and_prefers_whole_bean():
    now = datetime.now(UTC)
    variant_merch = SimpleNamespace(
        is_whole_bean=False,
        weight_grams=None,
        offers=[SimpleNamespace(observed_at=now, price_cents=1200)],
    )
    variant_bean = SimpleNamespace(
        is_whole_bean=True,
        weight_grams=340,
        offers=[SimpleNamespace(observed_at=now, price_cents=1800)],
    )
    product = SimpleNamespace(variants=[variant_merch, variant_bean])

    variant, latest_offer = _select_primary_variant(product)
    assert variant is variant_bean
    assert latest_offer.price_cents == 1800


def _seed_product(
    session: Session,
    merchant: Merchant,
    *,
    external_id: str,
    name: str,
    origin_country: str,
    process_family: str,
    roast_level: str,
    price_cents: int,
    compare_at_price_cents: int | None,
    is_available: bool,
    is_whole_bean: bool,
    weight_grams: int | None,
    category: str = "coffee",
) -> Product:
    now = datetime.now(UTC)
    product = Product(
        merchant_id=merchant.id,
        external_product_id=external_id,
        name=name,
        product_url=f"https://{merchant.canonical_domain}/products/{external_id}",
        image_url="",
        origin_text=origin_country,
        origin_country=origin_country,
        origin_country_confidence=0.9,
        origin_country_source="parser",
        process_text=process_family.title(),
        process_family=process_family,
        process_family_confidence=0.9,
        process_family_source="parser",
        roast_cues=roast_level,
        roast_level=roast_level,
        roast_level_confidence=0.9,
        roast_level_source="parser",
        metadata_confidence=0.9,
        metadata_source="parser",
        product_category=category,
        is_single_origin=True,
        is_espresso_recommended=roast_level in {"medium-dark", "dark"},
        is_active=True,
        first_seen_at=now,
        last_seen_at=now,
    )
    session.add(product)
    session.flush()

    variant = ProductVariant(
        product_id=product.id,
        external_variant_id=f"{external_id}-v1",
        label="12 oz",
        weight_grams=weight_grams,
        is_whole_bean=is_whole_bean,
        is_available=is_available,
        first_seen_at=now,
        last_seen_at=now,
    )
    session.add(variant)
    session.flush()

    session.add(
        OfferSnapshot(
            variant_id=variant.id,
            observed_at=now,
            price_cents=price_cents,
            compare_at_price_cents=compare_at_price_cents,
            subscription_price_cents=None,
            is_on_sale=bool(compare_at_price_cents and compare_at_price_cents > price_cents),
            is_available=is_available,
            source_url=product.product_url,
        )
    )
    session.flush()
    return product


@pytest.fixture()
def catalog_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        alpha = Merchant(
            name="Alpha Coffee",
            canonical_domain="alpha.example",
            homepage_url="https://alpha.example",
            platform_type="shopify",
        )
        beta = Merchant(
            name="Beta Roasters",
            canonical_domain="beta.example",
            homepage_url="https://beta.example",
            platform_type="shopify",
        )
        session.add_all([alpha, beta])
        session.flush()

        bourbon_sunset = _seed_product(
            session,
            alpha,
            external_id="bourbon-sunset",
            name="Bourbon Sunset",
            origin_country="Colombia",
            process_family="washed",
            roast_level="medium-dark",
            price_cents=2600,
            compare_at_price_cents=3200,
            is_available=True,
            is_whole_bean=True,
            weight_grams=340,
        )
        citrus_bloom = _seed_product(
            session,
            beta,
            external_id="citrus-bloom",
            name="Citrus Bloom",
            origin_country="Ethiopia",
            process_family="washed",
            roast_level="light",
            price_cents=1800,
            compare_at_price_cents=None,
            is_available=True,
            is_whole_bean=True,
            weight_grams=340,
        )
        kenya_nightjar = _seed_product(
            session,
            alpha,
            external_id="kenya-nightjar",
            name="Kenya Nightjar",
            origin_country="Kenya",
            process_family="natural",
            roast_level="light-medium",
            price_cents=2200,
            compare_at_price_cents=None,
            is_available=False,
            is_whole_bean=True,
            weight_grams=340,
        )
        ground_house = _seed_product(
            session,
            beta,
            external_id="ground-house",
            name="Ground House",
            origin_country="Brazil",
            process_family="blend",
            roast_level="medium",
            price_cents=1900,
            compare_at_price_cents=None,
            is_available=True,
            is_whole_bean=False,
            weight_grams=None,
        )
        ids = {
            "alpha": alpha.id,
            "beta": beta.id,
            "bourbon_sunset": bourbon_sunset.id,
            "citrus_bloom": citrus_bloom.id,
            "kenya_nightjar": kenya_nightjar.id,
            "ground_house": ground_house.id,
        }
        session.commit()

    app = FastAPI()
    app.include_router(products_router, prefix="/api/v1")

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client, ids

    app.dependency_overrides.clear()


def test_search_products_filters_by_server_side_catalog_fields(catalog_client) -> None:
    client, ids = catalog_client

    response = client.get(
        "/api/v1/products/search",
        params={
            "merchant_id": str(ids["beta"]),
            "category": "coffee",
            "origin_country": "Ethiopia",
            "process_family": "washed",
            "roast_level": "light",
            "in_stock": "true",
            "whole_bean_only": "true",
            "on_sale": "false",
            "price_per_oz_max": "1.60",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["name"] for item in payload["items"]] == ["Citrus Bloom"]
    item = payload["items"][0]
    assert item["canonical_metadata"]["origin_country"]["value"] == "Ethiopia"
    assert item["canonical_metadata"]["origin_country"]["source"] == "parser"
    assert item["canonical_metadata"]["process_family"]["value"] == "washed"
    assert item["canonical_metadata"]["roast_level"]["value"] == "light"
    assert payload["has_more"] is False


def test_search_products_supports_stock_sale_and_non_whole_bean_filters(catalog_client) -> None:
    client, _ids = catalog_client

    sold_out = client.get("/api/v1/products/search", params={"category": "coffee", "in_stock": "false"})
    assert sold_out.status_code == 200
    assert [item["name"] for item in sold_out.json()["items"]] == ["Kenya Nightjar"]

    on_sale = client.get("/api/v1/products/search", params={"category": "coffee", "on_sale": "true"})
    assert on_sale.status_code == 200
    assert [item["name"] for item in on_sale.json()["items"]] == ["Bourbon Sunset"]

    ground_only = client.get("/api/v1/products/search", params={"category": "coffee", "whole_bean_only": "false"})
    assert ground_only.status_code == 200
    assert [item["name"] for item in ground_only.json()["items"]] == ["Ground House"]


def test_search_products_sorts_globally_with_offset_cursor(catalog_client) -> None:
    client, ids = catalog_client

    first_page = client.get(
        "/api/v1/products/search",
        params={"category": "coffee", "whole_bean_only": "true", "sort": "price_low", "limit": 1},
    )

    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert [item["id"] for item in first_payload["items"]] == [ids["citrus_bloom"]]
    assert first_payload["next_cursor"] == 1
    assert first_payload["has_more"] is True

    second_page = client.get(
        "/api/v1/products/search",
        params={
            "category": "coffee",
            "whole_bean_only": "true",
            "sort": "price_low",
            "limit": 1,
            "cursor": first_payload["next_cursor"],
        },
    )

    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert [item["id"] for item in second_payload["items"]] == [ids["kenya_nightjar"]]
    assert second_payload["next_cursor"] == 2


def test_list_products_for_merchant_uses_server_side_sorting(catalog_client) -> None:
    client, ids = catalog_client

    response = client.get(
        f"/api/v1/merchants/{ids['alpha']}/products",
        params={"category": "coffee", "sort": "discount"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["name"] for item in payload["items"]] == ["Bourbon Sunset", "Kenya Nightjar"]


@pytest.fixture()
def deal_fact_client():
    """Catalog client with a VariantDealFact row seeded for the primary variant."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        merchant = Merchant(
            name="Deal Roasters",
            canonical_domain="deal.example",
            homepage_url="https://deal.example",
            platform_type="shopify",
        )
        session.add(merchant)
        session.flush()

        product = _seed_product(
            session,
            merchant,
            external_id="deal-coffee",
            name="Deal Coffee",
            origin_country="Colombia",
            process_family="washed",
            roast_level="medium",
            price_cents=1800,
            compare_at_price_cents=None,
            is_available=True,
            is_whole_bean=True,
            weight_grams=340,
        )
        # Fetch the variant that was created by _seed_product
        variant = session.scalars(
            __import__("sqlalchemy", fromlist=["select"]).select(ProductVariant).where(
                ProductVariant.product_id == product.id
            )
        ).first()
        assert variant is not None

        now = datetime.now(UTC)
        deal_fact = VariantDealFact(
            variant_id=variant.id,
            computed_at=now,
            offer_count=10,
            distinct_offer_days=30,
            current_price_cents=1800,
            baseline_7d_cents=2000,
            baseline_30d_cents=2100,
            historical_low_cents=1700,
            historical_high_cents=2400,
            compare_at_discount_percent=0.0,
            price_drop_7d_percent=10.0,
            price_drop_30d_percent=14.3,
        )
        session.add(deal_fact)
        session.commit()

        merchant_id = merchant.id
        product_id = product.id

    app = FastAPI()
    app.include_router(products_router, prefix="/api/v1")

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client, merchant_id, product_id

    app.dependency_overrides.clear()


def test_catalog_returns_deal_fact_fields_when_variant_deal_fact_exists(deal_fact_client) -> None:
    client, merchant_id, product_id = deal_fact_client

    # Test via merchant products endpoint
    response = client.get(
        f"/api/v1/merchants/{merchant_id}/products",
        params={"category": "coffee"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    item = payload["items"][0]

    deal = item.get("deal_fact")
    assert deal is not None, "deal_fact should be present when VariantDealFact row exists"
    assert deal["baseline_30d_cents"] == 2100
    assert deal["price_drop_30d_percent"] == pytest.approx(14.3, abs=0.1)
    assert deal["historical_low_cents"] == 1700


def test_catalog_search_returns_deal_fact_fields_when_variant_deal_fact_exists(deal_fact_client) -> None:
    client, merchant_id, _product_id = deal_fact_client

    response = client.get(
        "/api/v1/products/search",
        params={"merchant_id": str(merchant_id), "category": "coffee"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    deal = payload["items"][0].get("deal_fact")
    assert deal is not None
    assert deal["baseline_30d_cents"] == 2100


def test_catalog_returns_null_deal_fact_when_no_variant_deal_fact(catalog_client) -> None:
    client, ids = catalog_client

    # bourbon_sunset has no VariantDealFact seeded → deal_fact should be null
    response = client.get(
        "/api/v1/products/search",
        params={"category": "coffee", "origin_country": "Colombia"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    # deal_fact absent or null — no badge should be needed
    assert item.get("deal_fact") is None
