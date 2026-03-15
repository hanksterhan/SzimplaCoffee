"""SC-32: Auto-generate merchant quality profiles from observable data."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    CrawlRun,
    Merchant,
    MerchantQualityProfile,
    Product,
    ShippingPolicy,
)

# Keywords indicating freshness transparency in product descriptions
FRESHNESS_KEYWORDS = re.compile(
    r"\b(roast\s*date|roasted\s+to\s+order|roasted\s+on|fresh\s+roast|freshly\s+roast"
    r"|harvest\s+date|crop\s+year|just\s+roasted)\b",
    re.IGNORECASE,
)

# Weights for overall_quality_score
WEIGHTS = {
    "freshness_transparency_score": 0.25,
    "shipping_clarity_score": 0.15,
    "metadata_quality_score": 0.25,
    "espresso_relevance_score": 0.20,
    "service_confidence_score": 0.15,
}


def _score_freshness(session: Session, merchant: Merchant) -> float:
    """Score based on freshness/transparency signals in product data."""
    products = session.scalars(
        select(Product).where(Product.merchant_id == merchant.id, Product.is_active.is_(True))
    ).all()

    if not products:
        return 0.3  # Neutral-low: no data to assess

    freshness_hits = 0
    for p in products:
        combined_text = " ".join(
            filter(None, [p.roast_cues, p.tasting_notes_text, p.name])
        )
        if FRESHNESS_KEYWORDS.search(combined_text):
            freshness_hits += 1

    ratio = freshness_hits / len(products)

    # Also reward crawl recency — recent crawl means fresher data
    last_crawl = session.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant.id, CrawlRun.status == "completed")
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    recency_bonus = 0.0
    if last_crawl and last_crawl.started_at:
        ts = last_crawl.started_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        age_hours = (datetime.now(UTC) - ts).total_seconds() / 3600
        if age_hours < 6:
            recency_bonus = 0.1
        elif age_hours < 24:
            recency_bonus = 0.05

    raw = 0.3 + ratio * 0.6 + recency_bonus
    return min(1.0, raw)


def _score_shipping(session: Session, merchant: Merchant) -> float:
    """Score based on shipping policy completeness."""
    policies = session.scalars(
        select(ShippingPolicy).where(ShippingPolicy.merchant_id == merchant.id)
        .order_by(ShippingPolicy.observed_at.desc())
        .limit(5)
    ).all()

    if not policies:
        return 0.0

    # Use most-recent policy
    p = policies[0]
    score = 0.3  # Base: has a record

    if p.free_shipping_threshold_cents is not None:
        score += 0.25
    if p.estimated_delivery_days is not None:
        score += 0.20
    if p.shipping_notes and len(p.shipping_notes) > 20:
        score += 0.15
    if len(policies) > 1:
        score += 0.10  # Multiple observed policies = richer history

    return min(1.0, score)


def _score_metadata(session: Session, merchant: Merchant) -> float:
    """Score based on product metadata completeness."""
    products = session.scalars(
        select(Product).where(Product.merchant_id == merchant.id, Product.is_active.is_(True))
    ).all()

    if not products:
        return 0.0

    total = len(products)
    origin_count = sum(1 for p in products if p.origin_text and p.origin_text.strip())
    process_count = sum(1 for p in products if p.process_text and p.process_text.strip())
    notes_count = sum(1 for p in products if p.tasting_notes_text and p.tasting_notes_text.strip())

    origin_ratio = origin_count / total
    process_ratio = process_count / total
    notes_ratio = notes_count / total

    # Weighted: origin most important, then notes, then process
    return 0.4 * origin_ratio + 0.35 * notes_ratio + 0.25 * process_ratio


def _score_espresso_relevance(session: Session, merchant: Merchant) -> float:
    """Score based on espresso-focused product presence."""
    products = session.scalars(
        select(Product).where(Product.merchant_id == merchant.id, Product.is_active.is_(True))
    ).all()

    if not products:
        return 0.0

    total = len(products)
    espresso_flagged = sum(1 for p in products if p.is_espresso_recommended)

    # Also check names/descriptions for espresso mentions
    espresso_keyword = re.compile(r"\bespresso\b", re.IGNORECASE)
    espresso_mentioned = sum(
        1 for p in products if espresso_keyword.search(p.name or "")
    )

    flagged_ratio = espresso_flagged / total
    mention_ratio = espresso_mentioned / total

    return min(1.0, flagged_ratio * 0.7 + mention_ratio * 0.3)


def _score_service_confidence(session: Session, merchant: Merchant) -> float:
    """Score based on crawl success rate and data freshness."""
    all_runs = session.scalars(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant.id)
        .order_by(CrawlRun.started_at.desc())
        .limit(20)
    ).all()

    if not all_runs:
        return 0.3  # No data yet

    total = len(all_runs)
    completed = sum(1 for r in all_runs if r.status == "completed")
    success_rate = completed / total

    # Data freshness component
    last_success = next((r for r in all_runs if r.status == "completed"), None)
    freshness_score = 0.0
    if last_success and last_success.started_at:
        ts = last_success.started_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        age_hours = (datetime.now(UTC) - ts).total_seconds() / 3600
        if age_hours < 24:
            freshness_score = 1.0
        elif age_hours < 72:
            freshness_score = 0.7
        elif age_hours < 168:  # 7 days
            freshness_score = 0.4
        else:
            freshness_score = 0.1

    # Product count bonus (more products = higher confidence)
    product_count = session.scalar(
        select(func.count(Product.id)).where(
            Product.merchant_id == merchant.id, Product.is_active.is_(True)
        )
    ) or 0
    count_bonus = min(0.2, product_count * 0.005)  # Up to 0.2 at 40 products

    raw = success_rate * 0.5 + freshness_score * 0.3 + count_bonus
    return min(1.0, raw)


def compute_quality_scores(session: Session, merchant: Merchant) -> dict[str, float]:
    """Compute all quality scores for a merchant. Returns dict of score fields."""
    freshness = _score_freshness(session, merchant)
    shipping = _score_shipping(session, merchant)
    metadata = _score_metadata(session, merchant)
    espresso = _score_espresso_relevance(session, merchant)
    service = _score_service_confidence(session, merchant)

    overall = sum(
        score * WEIGHTS[key]
        for key, score in [
            ("freshness_transparency_score", freshness),
            ("shipping_clarity_score", shipping),
            ("metadata_quality_score", metadata),
            ("espresso_relevance_score", espresso),
            ("service_confidence_score", service),
        ]
    )

    return {
        "freshness_transparency_score": round(freshness, 4),
        "shipping_clarity_score": round(shipping, 4),
        "metadata_quality_score": round(metadata, 4),
        "espresso_relevance_score": round(espresso, 4),
        "service_confidence_score": round(service, 4),
        "overall_quality_score": round(overall, 4),
    }


def score_merchant(session: Session, merchant: Merchant) -> MerchantQualityProfile:
    """Compute and upsert quality profile for a single merchant."""
    scores = compute_quality_scores(session, merchant)

    profile = session.scalar(
        select(MerchantQualityProfile).where(
            MerchantQualityProfile.merchant_id == merchant.id
        )
    )

    if profile is None:
        profile = MerchantQualityProfile(merchant_id=merchant.id)
        session.add(profile)

    profile.freshness_transparency_score = scores["freshness_transparency_score"]
    profile.shipping_clarity_score = scores["shipping_clarity_score"]
    profile.metadata_quality_score = scores["metadata_quality_score"]
    profile.espresso_relevance_score = scores["espresso_relevance_score"]
    profile.service_confidence_score = scores["service_confidence_score"]
    profile.overall_quality_score = scores["overall_quality_score"]
    profile.last_reviewed_at = datetime.now(UTC)

    session.flush()
    return profile


def score_all_merchants(session: Session) -> list[dict]:
    """Score all active merchants and upsert their quality profiles."""
    merchants = session.scalars(
        select(Merchant).where(Merchant.is_active.is_(True))
    ).all()

    results = []
    for merchant in merchants:
        profile = score_merchant(session, merchant)
        results.append(
            {
                "merchant_id": merchant.id,
                "name": merchant.name,
                "freshness": profile.freshness_transparency_score,
                "shipping": profile.shipping_clarity_score,
                "metadata": profile.metadata_quality_score,
                "espresso": profile.espresso_relevance_score,
                "service": profile.service_confidence_score,
                "overall": profile.overall_quality_score,
            }
        )
    return results
