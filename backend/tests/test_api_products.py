from fastapi import Query

from szimplacoffee.api.products import _parse_categories, _coffee_like_merch_clause, _normalize_query_default
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
