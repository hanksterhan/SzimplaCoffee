from datetime import datetime, timedelta, UTC
from types import SimpleNamespace

from fastapi import Query

from szimplacoffee.api.products import (
    _coffee_like_merch_clause,
    _normalize_query_default,
    _parse_categories,
    _select_primary_variant,
    _variant_latest_offer,
)
from szimplacoffee.models import Product


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
