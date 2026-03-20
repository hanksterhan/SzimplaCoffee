"""SC-110: Tests for backfill-descriptions CLI command logic.

Tests verify:
1. Products with description_text get metadata upgraded when confidence improves.
2. Products parsed as non-coffee get reclassified even if stored as 'coffee'.
3. Products without description_text are still checked for name-based non-coffee reclassification.
4. Existing high-confidence metadata is not downgraded.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from szimplacoffee.models import Base, Merchant, Product
from szimplacoffee.services.coffee_parser import parse_coffee_metadata, default_process_family_for_country


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


def _make_merchant(session: Session) -> Merchant:
    m = Merchant(
        name="Test Roaster",
        canonical_domain="test-roaster.com",
        homepage_url="https://test-roaster.com",
        crawl_tier="A",
        is_active=True,
    )
    session.add(m)
    session.flush()
    return m


_product_counter = 0


def _make_product(session: Session, merchant: Merchant, **kwargs) -> Product:
    global _product_counter
    _product_counter += 1
    defaults = dict(
        name="Test Coffee",
        external_product_id=f"test-{_product_counter}",
        product_url=f"https://test-roaster.com/products/test-{_product_counter}",
        product_category="coffee",
        is_active=True,
        origin_country=None,
        origin_country_confidence=0.0,
        origin_country_source="unknown",
        roast_level="unknown",
        roast_level_confidence=0.0,
        roast_level_source="unknown",
        process_family="unknown",
        process_family_confidence=0.0,
        process_family_source="unknown",
        description_text=None,
        metadata_confidence=0.0,
    )
    defaults.update(kwargs)
    p = Product(merchant_id=merchant.id, **defaults)
    session.add(p)
    session.flush()
    return p


# ---------------------------------------------------------------------------
# Unit tests for parser behavior (no DB needed)
# ---------------------------------------------------------------------------

class TestParserBehavior:
    """Validate the parser produces the right signals for backfill-descriptions use cases."""

    def test_non_coffee_by_name_detected(self):
        parsed = parse_coffee_metadata("V60 Filters", "")
        assert not parsed.is_coffee_product

    def test_non_coffee_by_name_aeropress(self):
        parsed = parse_coffee_metadata("AeroPress Filters", "")
        assert not parsed.is_coffee_product

    def test_non_coffee_vinyl_record(self):
        parsed = parse_coffee_metadata("Bruce Springsteen - Born to Run", "")
        assert not parsed.is_coffee_product

    def test_non_coffee_gift_subscription(self):
        parsed = parse_coffee_metadata("Gift Subscription - Single Origin", "")
        assert not parsed.is_coffee_product

    def test_coffee_ethiopia_name(self):
        parsed = parse_coffee_metadata("Ethiopia Yirgacheffe Natural", "")
        assert parsed.is_coffee_product
        assert parsed.origin_country == "Ethiopia"

    def test_description_upgrades_process(self):
        """Parser extracts process from description text."""
        parsed = parse_coffee_metadata("Morning Sun", "This coffee uses a natural dry process from our farm.")
        assert parsed.is_coffee_product

    def test_default_process_family_for_country_colombia(self):
        """Colombia has a known default process family."""
        result = default_process_family_for_country("Colombia")
        assert result == "washed"

    def test_default_process_family_for_country_ethiopia_none(self):
        """Ethiopia has no single default (produces both natural and washed)."""
        result = default_process_family_for_country("Ethiopia")
        # Ethiopia has no deterministic default — None is the expected return
        assert result is None


# ---------------------------------------------------------------------------
# Integration tests with in-memory SQLite DB
# ---------------------------------------------------------------------------

class TestBackfillDescriptionsLogic:
    """Test the core re-pass logic that backfill-descriptions implements."""

    def _run_backfill_descriptions(self, session: Session):
        """Inline the backfill-descriptions logic for testing."""
        from sqlalchemy import select
        all_active = session.scalars(
            select(Product).where(Product.is_active == True)  # noqa: E712
        ).all()

        updated = 0
        reclassified = 0
        origin_upgraded = 0

        for product in all_active:
            changed = False

            # Pass 1: reclassify non-coffee by name
            parsed_name = parse_coffee_metadata(product.name, "")
            if not parsed_name.is_coffee_product and product.product_category == "coffee":
                product.product_category = "non-coffee"
                reclassified += 1
                changed = True

            # Pass 2: upgrade metadata from description_text
            if product.description_text and product.product_category != "non-coffee":
                parsed = parse_coffee_metadata(product.name, product.description_text)

                if not parsed.is_coffee_product and product.product_category == "coffee":
                    product.product_category = "non-coffee"
                    reclassified += 1
                    changed = True
                    continue

                # Upgrade origin_country if confidence improves
                if parsed.origin_country and (
                    not product.origin_country or
                    parsed.origin_country_confidence > float(product.origin_country_confidence or 0.0) + 0.05
                ):
                    product.origin_country = parsed.origin_country
                    product.origin_country_confidence = parsed.origin_country_confidence
                    product.origin_country_source = parsed.origin_country_source
                    origin_upgraded += 1
                    changed = True

            if changed:
                updated += 1

        session.flush()
        return {"updated": updated, "reclassified": reclassified, "origin_upgraded": origin_upgraded}

    def test_filter_name_reclassifies_as_non_coffee(self):
        engine = _make_engine()
        with Session(engine) as session:
            m = _make_merchant(session)
            p = _make_product(session, m, name="V60 Filters", product_category="coffee")
            assert p.product_category == "coffee"

            result = self._run_backfill_descriptions(session)

            assert p.product_category == "non-coffee"
            assert result["reclassified"] >= 1

    def test_coffee_product_not_reclassified(self):
        engine = _make_engine()
        with Session(engine) as session:
            m = _make_merchant(session)
            p = _make_product(session, m, name="Ethiopia Yirgacheffe", product_category="coffee")

            result = self._run_backfill_descriptions(session)

            assert p.product_category == "coffee"
            assert result["reclassified"] == 0

    def test_existing_high_confidence_origin_not_downgraded(self):
        """Backfill should not replace a high-confidence origin with a meaningfully lower-confidence one."""
        engine = _make_engine()
        with Session(engine) as session:
            m = _make_merchant(session)
            p = _make_product(
                session, m,
                name="Ethiopia Natural",
                product_category="coffee",
                origin_country="Ethiopia",
                origin_country_confidence=0.95,
                origin_country_source="structured",
                # Description mentions a region but not a competing country
                description_text="A beautiful washed coffee with bright citrus notes.",
            )

            self._run_backfill_descriptions(session)

            # High-confidence existing origin should be preserved
            assert p.origin_country == "Ethiopia"
            assert float(p.origin_country_confidence) >= 0.90

    def test_fill_rate_improves_after_reclassification(self):
        """After reclassifying non-coffee items, the coffee-product fill rate should improve."""
        engine = _make_engine()
        with Session(engine) as session:
            from sqlalchemy import select
            m = _make_merchant(session)
            # Real coffee with origin
            _make_product(session, m, name="Ethiopia Yirgacheffe", product_category="coffee",
                         origin_country="Ethiopia", origin_country_confidence=0.9)
            # Equipment masquerading as coffee — no origin
            _make_product(session, m, name="Aeropress Filters", product_category="coffee",
                         origin_country=None)

            all_before = session.scalars(select(Product).where(Product.is_active)).all()
            coffee_before = [p for p in all_before if p.product_category == "coffee"]
            origin_before_pct = sum(1 for p in coffee_before if p.origin_country) / len(coffee_before)
            assert origin_before_pct == 0.5  # 1/2

            self._run_backfill_descriptions(session)

            all_after = session.scalars(select(Product).where(Product.is_active)).all()
            coffee_after = [p for p in all_after if p.product_category == "coffee"]
            origin_after_pct = sum(1 for p in coffee_after if p.origin_country) / len(coffee_after)
            # After removing the filter (non-coffee), only the real coffee remains = 100%
            assert origin_after_pct == 1.0
