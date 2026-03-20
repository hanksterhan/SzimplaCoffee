"""SC-112: Tests for why_text generation in recommendation service."""
from __future__ import annotations

from unittest.mock import MagicMock

from szimplacoffee.services.recommendations import _build_why_text


def _mock_product(
    *,
    origin_country: str | None = None,
    origin_text: str | None = None,
    process_family: str | None = None,
    process_text: str | None = None,
) -> MagicMock:
    p = MagicMock()
    p.origin_country = origin_country
    p.origin_text = origin_text
    p.process_family = process_family
    p.process_text = process_text
    return p


class TestBuildWhyText:
    def test_great_deal_with_30d_drop_produces_deal_sentence(self):
        product = _mock_product(origin_country="Ethiopia", process_family="Washed")
        text = _build_why_text(
            merchant_name="Some Roaster",
            product=product,
            deal_badge="great_deal",
            deal_fact_price_drop_30d_percent=18.0,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=1200,
            deal_fact_baseline_30d_cents=1500,
            merchant_score=0.75,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert "18%" in text
        assert "30-day" in text
        assert text.strip().endswith(".")

    def test_good_deal_badge_produces_deal_sentence(self):
        product = _mock_product(origin_country="Colombia")
        text = _build_why_text(
            merchant_name="Roaster",
            product=product,
            deal_badge="good_deal",
            deal_fact_price_drop_30d_percent=7.5,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.72,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert "7%" in text or "7.5%" in text or "8%" in text  # integer formatted
        assert text.strip().endswith(".")

    def test_highly_rated_merchant_mentioned(self):
        product = _mock_product()
        text = _build_why_text(
            merchant_name="Elite Roasters",
            product=product,
            deal_badge="at_baseline",
            deal_fact_price_drop_30d_percent=0.0,
            deal_fact_compare_at_discount_percent=0.0,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.85,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert "Elite Roasters" in text
        assert "highly-rated" in text or "trusted" in text

    def test_brew_feedback_mentioned_when_multiple_sessions(self):
        product = _mock_product(origin_country="Guatemala")
        text = _build_why_text(
            merchant_name="Roaster",
            product=product,
            deal_badge="at_baseline",
            deal_fact_price_drop_30d_percent=0.0,
            deal_fact_compare_at_discount_percent=0.0,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.68,
            brew_session_count=3,
            brew_avg_rating=8.8,
        )
        assert "8.8" in text
        assert "sessions" in text

    def test_origin_mentioned_in_output(self):
        product = _mock_product(origin_country="Kenya", process_family="Washed")
        text = _build_why_text(
            merchant_name="Roaster",
            product=product,
            deal_badge="no_baseline",
            deal_fact_price_drop_30d_percent=None,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.72,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert "Kenya" in text

    def test_process_mentioned_in_output(self):
        product = _mock_product(process_family="Natural")
        text = _build_why_text(
            merchant_name="Roaster",
            product=product,
            deal_badge="no_baseline",
            deal_fact_price_drop_30d_percent=None,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.72,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert "natural" in text.lower()

    def test_no_signals_returns_fallback(self):
        product = _mock_product()
        text = _build_why_text(
            merchant_name="Unknown",
            product=product,
            deal_badge="no_baseline",
            deal_fact_price_drop_30d_percent=None,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.50,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        assert len(text) > 0
        assert text.strip().endswith(".")

    def test_compare_at_discount_used_when_no_30d_drop(self):
        product = _mock_product(origin_country="Brazil")
        text = _build_why_text(
            merchant_name="Roaster",
            product=product,
            deal_badge="great_deal",
            deal_fact_price_drop_30d_percent=1.0,  # small — shouldn't dominate
            deal_fact_compare_at_discount_percent=22.0,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.72,
            brew_session_count=0,
            brew_avg_rating=None,
        )
        # For great_deal: price_drop_30d_percent=1.0 < 5, so it should fall through to compare_at
        assert "22%" in text

    def test_output_is_plain_text_no_newlines(self):
        product = _mock_product(origin_country="Peru", process_family="Honey")
        text = _build_why_text(
            merchant_name="Good Roaster",
            product=product,
            deal_badge="good_deal",
            deal_fact_price_drop_30d_percent=8.0,
            deal_fact_compare_at_discount_percent=None,
            deal_fact_historical_low_cents=None,
            deal_fact_baseline_30d_cents=None,
            merchant_score=0.80,
            brew_session_count=1,
            brew_avg_rating=9.0,
        )
        assert "\n" not in text
        assert len(text) < 300
