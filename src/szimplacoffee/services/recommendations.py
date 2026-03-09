from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Merchant, MerchantPersonalProfile, MerchantQualityProfile, OfferSnapshot, Product, ProductVariant, RecommendationRun, ShippingPolicy


QuantityMode = Literal["12-18 oz", "2 lb", "5 lb", "any"]
ShotStyle = Literal["modern_58mm", "cremina_49mm", "turbo", "experimental"]


@dataclass
class RecommendationRequest:
    shot_style: ShotStyle
    quantity_mode: QuantityMode
    bulk_allowed: bool


@dataclass
class RecommendationCandidate:
    merchant_name: str
    product_name: str
    variant_label: str
    product_url: str
    weight_grams: int | None
    landed_price_cents: int
    score: float
    rationale: list[str]


def _latest_offer(session: Session, variant_id: int) -> OfferSnapshot | None:
    return session.scalar(
        select(OfferSnapshot)
        .where(OfferSnapshot.variant_id == variant_id)
        .order_by(OfferSnapshot.observed_at.desc())
        .limit(1)
    )


def _latest_shipping_policy(session: Session, merchant_id: int) -> ShippingPolicy | None:
    return session.scalar(
        select(ShippingPolicy)
        .where(ShippingPolicy.merchant_id == merchant_id)
        .order_by(ShippingPolicy.observed_at.desc())
        .limit(1)
    )


def _merchant_quality_score(merchant: Merchant) -> float:
    quality = merchant.quality_profile.overall_quality_score if merchant.quality_profile else 0.5
    personal = merchant.personal_profile.personal_trust_score if merchant.personal_profile else 0.5
    return (quality * 0.55) + (personal * 0.45)


def _quantity_target(quantity_mode: QuantityMode) -> tuple[int, int]:
    mapping = {
        "12-18 oz": (340, 510),
        "2 lb": (800, 1100),
        "5 lb": (1900, 2600),
        "any": (0, 5000),
    }
    return mapping[quantity_mode]


def _quantity_score(weight_grams: int | None, quantity_mode: QuantityMode, bulk_allowed: bool) -> float:
    if quantity_mode == "any":
        return 0.8
    if weight_grams is None:
        return 0.4
    lower, upper = _quantity_target(quantity_mode)
    if lower <= weight_grams <= upper:
        return 1.0
    if not bulk_allowed and weight_grams > upper:
        return 0.1
    if weight_grams < lower:
        return max(0.2, weight_grams / lower)
    overshoot = weight_grams - upper
    return max(0.15, 1.0 - (overshoot / max(upper, 1)))


def _espresso_fit(product: Product, shot_style: ShotStyle) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.55
    process = product.process_text.lower()
    notes = product.tasting_notes_text.lower()
    if product.is_espresso_recommended:
        score += 0.15
        reasons.append("merchant signals espresso suitability")
    if "washed" in process:
        score += 0.12
        reasons.append("washed process tends to suit clean espresso well")
    if "anaerobic" in process:
        score += 0.05
        reasons.append("cleaner anaerobic lots can still work well here")
    if shot_style == "turbo" and "washed" in process:
        score += 0.08
        reasons.append("turbo mode prefers clean, high-clarity coffees")
    if shot_style == "cremina_49mm" and "anaerobic" in process:
        score -= 0.03
    if "blackberry" in notes or "citrus" in notes or "floral" in notes:
        score += 0.04
    return min(score, 1.0), reasons


def _landed_price_cents(offer: OfferSnapshot, shipping_policy: ShippingPolicy | None) -> int:
    if shipping_policy and shipping_policy.free_shipping_threshold_cents and offer.price_cents >= shipping_policy.free_shipping_threshold_cents:
        return offer.price_cents
    return offer.price_cents + 800


def _deal_score(offer: OfferSnapshot, variant: ProductVariant, shipping_policy: ShippingPolicy | None) -> tuple[float, int, list[str]]:
    landed = _landed_price_cents(offer, shipping_policy)
    reasons: list[str] = []
    if shipping_policy and shipping_policy.free_shipping_threshold_cents and offer.price_cents >= shipping_policy.free_shipping_threshold_cents:
        reasons.append("qualifies for free shipping")
    if offer.compare_at_price_cents and offer.compare_at_price_cents > offer.price_cents:
        reasons.append("current price is below compare-at price")
    if not variant.weight_grams:
        return 0.45, landed, reasons
    cents_per_gram = landed / variant.weight_grams
    if cents_per_gram <= 6:
        return 1.0, landed, reasons
    if cents_per_gram <= 8:
        return 0.8, landed, reasons
    if cents_per_gram <= 10:
        return 0.6, landed, reasons
    return 0.35, landed, reasons


def build_recommendations(session: Session, request: RecommendationRequest) -> list[RecommendationCandidate]:
    candidates: list[RecommendationCandidate] = []
    products = session.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())).all()

    for product in products:
        merchant = product.merchant
        merchant_score = _merchant_quality_score(merchant)
        shipping_policy = _latest_shipping_policy(session, merchant.id)
        for variant in product.variants:
            if not variant.is_whole_bean:
                continue
            offer = _latest_offer(session, variant.id)
            if offer is None or not offer.is_available:
                continue

            quantity_score = _quantity_score(variant.weight_grams, request.quantity_mode, request.bulk_allowed)
            espresso_score, espresso_reasons = _espresso_fit(product, request.shot_style)
            deal_score, landed, deal_reasons = _deal_score(offer, variant, shipping_policy)
            freshness_score = merchant.quality_profile.freshness_transparency_score if merchant.quality_profile else 0.5

            total = (
                merchant_score * 0.30
                + quantity_score * 0.20
                + espresso_score * 0.25
                + deal_score * 0.15
                + freshness_score * 0.10
            )

            rationale = [
                f"merchant trust score {merchant_score:.2f}",
                f"quantity fit score {quantity_score:.2f}",
                f"deal score {deal_score:.2f}",
            ]
            rationale.extend(espresso_reasons[:2])
            rationale.extend(deal_reasons[:2])

            candidates.append(
                RecommendationCandidate(
                    merchant_name=merchant.name,
                    product_name=product.name,
                    variant_label=variant.label,
                    product_url=product.product_url,
                    weight_grams=variant.weight_grams,
                    landed_price_cents=landed,
                    score=round(total, 4),
                    rationale=rationale,
                )
            )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:5]


def persist_recommendation_run(session: Session, request: RecommendationRequest, candidates: list[RecommendationCandidate]) -> None:
    top_result = candidates[0] if candidates else None
    run = RecommendationRun(
        request_json=str(request.__dict__),
        top_result_json=str(top_result.__dict__ if top_result else {}),
        alternatives_json=str([candidate.__dict__ for candidate in candidates[1:3]]),
        wait_recommendation=not bool(candidates),
        model_version="v1",
    )
    session.add(run)
