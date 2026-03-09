from __future__ import annotations

from szimplacoffee.services.recommendations import RecommendationRequest, _quantity_score


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

