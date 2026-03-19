from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .db import Base, _apply_lightweight_migrations, engine
from .models import BrewFeedback, Merchant, MerchantPersonalProfile, MerchantQualityProfile, MerchantSource, PurchaseHistory, RecommendationRun
from .services.crawlers import crawl_merchant
from .services.platforms import detect_platform, normalize_url


def init_db() -> None:
    Base.metadata.create_all(engine)
    _apply_lightweight_migrations()
    _normalize_merchant_urls()


def _normalize_merchant_urls() -> None:
    """Idempotently normalize homepage_url for all existing merchants."""
    with Session(engine) as session:
        for merchant in session.scalars(select(Merchant)).all():
            normalized = normalize_url(merchant.homepage_url)
            if normalized != merchant.homepage_url:
                merchant.homepage_url = normalized
        session.commit()


def bootstrap_if_empty(session: Session) -> None:
    merchant_count = len(session.scalars(select(Merchant.id)).all())
    if merchant_count > 0:
        return

    seeds = [
        {
            "url": "https://www.olympiacoffee.com",
            "crawl_tier": "A",
            "trust_tier": "trusted",
            "quality": 0.92,
            "personal": 0.94,
            "notes": "Trusted clean light-roast profile; strong espresso relevance.",
        },
        {
            "url": "https://cambercoffee.com",
            "crawl_tier": "A",
            "trust_tier": "trusted",
            "quality": 0.90,
            "personal": 0.90,
            "notes": "Trusted Washington roaster with good single origin coverage.",
        },
    ]

    for seed in seeds:
        detection = detect_platform(seed["url"])
        merchant = Merchant(
            name=detection.merchant_name,
            canonical_domain=detection.domain,
            homepage_url=detection.normalized_url,
            platform_type=detection.platform_type,
            crawl_tier=seed["crawl_tier"],
            trust_tier=seed["trust_tier"],
        )
        session.add(merchant)
        session.flush()

        session.add(
            MerchantSource(
                merchant_id=merchant.id,
                source_type="seed",
                source_value=seed["url"],
                confidence=detection.confidence,
            )
        )
        session.add(
            MerchantQualityProfile(
                merchant_id=merchant.id,
                freshness_transparency_score=seed["quality"],
                shipping_clarity_score=0.85,
                metadata_quality_score=0.88,
                espresso_relevance_score=0.9,
                service_confidence_score=0.9,
                overall_quality_score=seed["quality"],
            )
        )
        session.add(
            MerchantPersonalProfile(
                merchant_id=merchant.id,
                has_order_history=True,
                would_reorder=True,
                personal_trust_score=seed["personal"],
                average_rating=9.0,
                notes=seed["notes"],
            )
        )
        session.flush()
        crawl_merchant(session, merchant)

    _seed_purchase_history(session)


def _seed_purchase_history(session: Session) -> None:
    merchants = {merchant.canonical_domain: merchant for merchant in session.scalars(select(Merchant)).all()}
    if not merchants:
        return

    records = [
        {
            "merchant_key": "olympiacoffee.com",
            "product_name": "Mikuba Anaerobic Natural",
            "origin_text": "Burundi",
            "process_text": "Anaerobic Natural",
            "price_cents": 5499,
            "weight_grams": 907,
            "purchased_at": datetime(2025, 7, 25, tzinfo=UTC),
            "feedback": {
                "shot_style": "modern_58mm",
                "grinder": "Timemore Sculptor 078S",
                "basket": "58mm",
                "rating": 10,
                "would_rebuy": True,
                "difficulty_score": 0.25,
                "notes": "Delicious, trusted Olympia profile.",
            },
        },
        {
            "merchant_key": "olympiacoffee.com",
            "product_name": "Kianyangi",
            "origin_text": "Kenya",
            "process_text": "Washed",
            "price_cents": 4920,
            "weight_grams": 907,
            "purchased_at": datetime(2024, 9, 13, tzinfo=UTC),
            "feedback": {
                "shot_style": "cremina_49mm",
                "grinder": "Timemore Sculptor 078S",
                "basket": "49mm",
                "rating": 7,
                "would_rebuy": False,
                "difficulty_score": 0.8,
                "notes": "Dense beans, harder to dial.",
            },
        },
        {
            "merchant_key": "cambercoffee.com",
            "product_name": "Ethiopia Banko Taratu",
            "origin_text": "Ethiopia",
            "process_text": "Washed",
            "price_cents": 2400,
            "weight_grams": 340,
            "purchased_at": datetime(2025, 9, 26, tzinfo=UTC),
            "feedback": {
                "shot_style": "modern_58mm",
                "grinder": "Timemore Sculptor 078S",
                "basket": "58mm",
                "rating": 8.5,
                "would_rebuy": True,
                "difficulty_score": 0.35,
                "notes": "Good washed Ethiopia anchor.",
            },
        },
    ]

    for record in records:
        merchant = merchants.get(record["merchant_key"])
        if not merchant:
            continue
        purchase = PurchaseHistory(
            merchant_id=merchant.id,
            product_name=record["product_name"],
            origin_text=record["origin_text"],
            process_text=record["process_text"],
            price_cents=record["price_cents"],
            weight_grams=record["weight_grams"],
            purchased_at=record["purchased_at"],
            source_system="seed",
            source_ref="bean-db-seed",
        )
        session.add(purchase)
        session.flush()
        feedback = record["feedback"]
        session.add(
            BrewFeedback(
                purchase_id=purchase.id,
                shot_style=feedback["shot_style"],
                grinder=feedback["grinder"],
                basket=feedback["basket"],
                rating=feedback["rating"],
                would_rebuy=feedback["would_rebuy"],
                difficulty_score=feedback["difficulty_score"],
                notes=feedback["notes"],
            )
        )


def seed_purchases() -> None:
    """Seed additional purchase records to reach ≥10 rows in purchase_history.

    Idempotent: does nothing if the table already has ≥10 rows.
    At least 3 of the new purchases are linked to existing recommendation_run_ids.
    """
    with Session(engine) as session:
        current_count = session.execute(text("SELECT COUNT(*) FROM purchase_history")).scalar() or 0
        if current_count >= 10:
            print(f"Already have {current_count} purchases — skipping seed.")
            return

        # Fetch merchant IDs
        merchants = {m.canonical_domain: m for m in session.scalars(select(Merchant)).all()}
        olympia = merchants.get("olympiacoffee.com")
        camber = merchants.get("cambercoffee.com")
        onyx = merchants.get("onyxcoffeelab.com")

        # Fetch existing recommendation run IDs
        run_ids = [r.id for r in session.scalars(select(RecommendationRun)).all()]
        run_id_1 = run_ids[0] if len(run_ids) > 0 else None
        run_id_2 = run_ids[1] if len(run_ids) > 1 else run_id_1

        new_purchases: list[dict] = [
            # 3 linked to recommendation runs
            {
                "merchant": olympia,
                "product_name": "Colombia Sebastian Ramirez Gesha White Honey",
                "origin_text": "Colombia",
                "process_text": "White Honey",
                "price_cents": 2700,
                "weight_grams": 227,
                "purchased_at": datetime(2025, 11, 3, tzinfo=UTC),
                "recommendation_run_id": run_id_1,
                "source_ref": "rec-run-seed",
            },
            {
                "merchant": camber,
                "product_name": "Rwanda Tumba",
                "origin_text": "Rwanda",
                "process_text": "Washed",
                "price_cents": 2100,
                "weight_grams": 340,
                "purchased_at": datetime(2025, 12, 10, tzinfo=UTC),
                "recommendation_run_id": run_id_1,
                "source_ref": "rec-run-seed",
            },
            {
                "merchant": olympia,
                "product_name": "Kenya Boma AA Micro Lot 12",
                "origin_text": "Kenya",
                "process_text": "Washed",
                "price_cents": 3200,
                "weight_grams": 454,
                "purchased_at": datetime(2026, 1, 5, tzinfo=UTC),
                "recommendation_run_id": run_id_2,
                "source_ref": "rec-run-seed",
            },
            # 2 organic / no rec link
            {
                "merchant": onyx or olympia,
                "product_name": "Geometry Espresso Blend",
                "origin_text": "Brazil/Ethiopia",
                "process_text": "Natural/Washed",
                "price_cents": 1950,
                "weight_grams": 340,
                "purchased_at": datetime(2026, 2, 14, tzinfo=UTC),
                "recommendation_run_id": None,
                "source_ref": "manual-seed",
            },
            {
                "merchant": camber or olympia,
                "product_name": "Camber Flagship Espresso",
                "origin_text": "Ethiopia/Colombia",
                "process_text": "Washed",
                "price_cents": 2200,
                "weight_grams": 340,
                "purchased_at": datetime(2026, 3, 1, tzinfo=UTC),
                "recommendation_run_id": None,
                "source_ref": "manual-seed",
            },
        ]

        added = 0
        for record in new_purchases:
            merchant = record["merchant"]
            if merchant is None:
                continue
            purchase = PurchaseHistory(
                merchant_id=merchant.id,
                product_name=record["product_name"],
                origin_text=record["origin_text"],
                process_text=record["process_text"],
                price_cents=record["price_cents"],
                weight_grams=record["weight_grams"],
                purchased_at=record["purchased_at"],
                source_system="seed",
                source_ref=record["source_ref"],
                recommendation_run_id=record["recommendation_run_id"],
            )
            session.add(purchase)
            added += 1

        session.commit()

        final_count = session.execute(text("SELECT COUNT(*) FROM purchase_history")).scalar() or 0
        linked = session.execute(
            text("SELECT COUNT(*) FROM purchase_history WHERE recommendation_run_id IS NOT NULL")
        ).scalar() or 0
        print(f"Seeded {added} purchases. Total: {final_count}, Linked to rec runs: {linked}")
