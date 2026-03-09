from __future__ import annotations

from szimplacoffee.services.discovery import _decode_bing_result_url
from szimplacoffee.services.recommendations import RecommendationRequest, _espresso_fit, _quantity_score
from szimplacoffee.services.crawlers import _is_coffee_product, _normalize_single_origin_flag


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
