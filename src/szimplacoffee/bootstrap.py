from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, engine
from .models import BrewFeedback, Merchant, MerchantPersonalProfile, MerchantQualityProfile, MerchantSource, PurchaseHistory
from .services.crawlers import crawl_merchant
from .services.platforms import detect_platform


def init_db() -> None:
    Base.metadata.create_all(engine)


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
