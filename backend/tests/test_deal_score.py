"""SC-109: Tests for baseline deal_score computation, badge assignment, and blended ranking."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from szimplacoffee.services.recommendations import (
    DEAL_BLEND_WEIGHT,
    QUALITY_BLEND_WEIGHT,
    _baseline_deal_score,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_baseline(median_price_cents: int):
    """Return a minimal VariantPriceBaseline-like mock."""
    b = MagicMock()
    b.median_price_cents = median_price_cents
    return b


# ---------------------------------------------------------------------------
# _baseline_deal_score — unit tests (no DB)
# ---------------------------------------------------------------------------

class TestBaselineDealScore:
    """Test _baseline_deal_score with mocked session.scalar."""

    def _call(self, session, variant_id: int, current_price_cents: int):
        return _baseline_deal_score(session, variant_id, current_price_cents)

    def _mock_session(self, baseline):
        session = MagicMock(spec=Session)
        session.scalar.return_value = baseline
        return session

    def test_no_baseline_returns_none_and_no_baseline_badge(self):
        session = self._mock_session(None)
        score, badge = self._call(session, 1, 1000)
        assert score is None
        assert badge == "no_baseline"

    def test_zero_median_returns_none(self):
        session = self._mock_session(_make_baseline(0))
        score, badge = self._call(session, 1, 1000)
        assert score is None
        assert badge == "no_baseline"

    def test_great_deal_when_20pct_below_baseline(self):
        """Price is 20% below baseline → great_deal."""
        baseline_cents = 1000
        current_price = int(baseline_cents * 0.80)  # $8.00 vs $10.00 → 20% below
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, current_price)
        assert score is not None
        assert score == pytest.approx(0.20, abs=0.001)
        assert badge == "great_deal"

    def test_good_deal_when_10pct_below_baseline(self):
        """Price is 10% below baseline → good_deal."""
        baseline_cents = 1000
        current_price = int(baseline_cents * 0.90)
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, current_price)
        assert score is not None
        assert score == pytest.approx(0.10, abs=0.001)
        assert badge == "good_deal"

    def test_at_baseline_when_equal(self):
        """Price equals baseline → at_baseline."""
        baseline_cents = 1200
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, baseline_cents)
        assert score is not None
        assert score == pytest.approx(0.0, abs=0.001)
        assert badge == "at_baseline"

    def test_above_baseline_when_10pct_above(self):
        """Price is 10% above baseline → above_baseline."""
        baseline_cents = 1000
        current_price = int(baseline_cents * 1.10)
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, current_price)
        assert score is not None
        assert score < 0
        assert badge == "above_baseline"

    def test_deal_score_clamped_to_minus_one(self):
        """Extremely overpriced: current_price >> baseline → clamp at -1.0."""
        baseline_cents = 500
        current_price = 5000  # 10x baseline
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, current_price)
        assert score == -1.0
        assert badge == "above_baseline"

    def test_deal_score_clamped_to_plus_one(self):
        """Free product (price = 0) → clamp at 1.0."""
        baseline_cents = 1000
        session = self._mock_session(_make_baseline(baseline_cents))
        score, badge = self._call(session, 1, 0)
        assert score == 1.0
        assert badge == "great_deal"


# ---------------------------------------------------------------------------
# Badge threshold boundary tests
# ---------------------------------------------------------------------------

class TestDealBadgeBoundaries:
    """Verify badge thresholds at exact boundary values."""

    def _score_for_pct(self, pct_below: float) -> tuple[float | None, str | None]:
        """Compute badge for a price that is pct_below % below $10.00 baseline."""
        baseline = 1000
        current = int(baseline * (1 - pct_below / 100))
        session = MagicMock(spec=Session)
        session.scalar.return_value = _make_baseline(baseline)
        return _baseline_deal_score(session, 1, current)

    def test_exactly_15pct_below_is_great_deal(self):
        _, badge = self._score_for_pct(15)
        assert badge == "great_deal"

    def test_14pct_below_is_good_deal(self):
        _, badge = self._score_for_pct(14)
        assert badge == "good_deal"

    def test_5pct_below_is_good_deal(self):
        _, badge = self._score_for_pct(5)
        assert badge == "good_deal"

    def test_3pct_below_is_at_baseline(self):
        _, badge = self._score_for_pct(3)
        assert badge == "at_baseline"

    def test_5pct_above_is_above_baseline(self):
        # 5% above means current = 1050, baseline = 1000
        # deal_score = (1000 - 1050) / 1000 = -0.05 → threshold is > -0.05 for at_baseline
        # so exactly -0.05 → above_baseline
        session = MagicMock(spec=Session)
        session.scalar.return_value = _make_baseline(1000)
        score, badge = _baseline_deal_score(session, 1, 1050)
        assert score == pytest.approx(-0.05, abs=0.001)
        assert badge == "above_baseline"


# ---------------------------------------------------------------------------
# Blended ranking weight constants
# ---------------------------------------------------------------------------

class TestBlendConstants:
    def test_quality_plus_deal_weights_sum_to_one(self):
        assert QUALITY_BLEND_WEIGHT + DEAL_BLEND_WEIGHT == pytest.approx(1.0, abs=0.001)

    def test_quality_weight_dominates(self):
        assert QUALITY_BLEND_WEIGHT > DEAL_BLEND_WEIGHT

    def test_deal_weight_is_positive(self):
        assert DEAL_BLEND_WEIGHT > 0


# ---------------------------------------------------------------------------
# Blended ranking: product with higher deal_score ranks above equal-quality competitor
# ---------------------------------------------------------------------------

class TestBlendedRanking:
    """Verify blended score formula applied manually gives expected ordering."""

    def _blended(self, quality_score: float, deal_score: float | None) -> float:
        deal_contribution = max(0.0, deal_score or 0.0)
        return QUALITY_BLEND_WEIGHT * quality_score + DEAL_BLEND_WEIGHT * deal_contribution

    def test_equal_quality_higher_deal_ranks_above(self):
        """Two coffees with same quality score — the one with better deal should rank higher."""
        quality = 0.75
        score_with_deal = self._blended(quality, 0.20)   # great_deal
        score_without_deal = self._blended(quality, 0.0)  # at_baseline
        assert score_with_deal > score_without_deal

    def test_no_baseline_is_neutral_not_penalised(self):
        """No baseline (None) must not hurt ranking compared to at_baseline (0)."""
        quality = 0.75
        score_none = self._blended(quality, None)
        score_zero = self._blended(quality, 0.0)
        assert score_none == score_zero, "None deal_score should be treated as 0 contribution"

    def test_above_baseline_does_not_boost_score(self):
        """Negative deal_score (above baseline) must not boost the blended total."""
        quality = 0.75
        score_above = self._blended(quality, -0.10)  # above_baseline
        score_neutral = self._blended(quality, 0.0)
        # max(0, negative) = 0, so blended score equals neutral
        assert score_above == score_neutral
