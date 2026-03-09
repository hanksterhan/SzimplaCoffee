from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BrewFeedback, Merchant, OfferSnapshot, Product, ProductVariant, PromoSnapshot, PurchaseHistory, RecommendationRun, ShippingPolicy


QuantityMode = Literal["12-18 oz", "2 lb", "5 lb", "any"]
ShotStyle = Literal["modern_58mm", "cremina_49mm", "turbo", "experimental"]


@dataclass
class RecommendationRequest:
    shot_style: ShotStyle
    quantity_mode: QuantityMode
    bulk_allowed: bool
    allow_decaf: bool = False


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


def _merchant_score_with_shot_style(merchant: Merchant, shot_style: ShotStyle) -> float:
    score = _merchant_quality_score(merchant)
    if shot_style == "cremina_49mm" and merchant.personal_profile:
        score += (merchant.personal_profile.personal_trust_score - 0.5) * 0.08
    if shot_style == "experimental" and merchant.quality_profile:
        score += (merchant.quality_profile.metadata_quality_score - 0.5) * 0.06
    return max(0.0, min(score, 1.0))


def _preference_profile(session: Session) -> dict:
    purchases = session.scalars(select(PurchaseHistory)).all()
    liked_merchants: set[int] = set()
    liked_processes: set[str] = set()
    liked_origins: set[str] = set()
    prefers_single_origin = True

    for purchase in purchases:
        feedback = purchase.brew_feedback[0] if purchase.brew_feedback else None
        if feedback and feedback.rating >= 8:
            liked_merchants.add(purchase.merchant_id)
            if purchase.process_text:
                liked_processes.add(purchase.process_text.lower())
            if purchase.origin_text:
                liked_origins.add(purchase.origin_text.lower())
    return {
        "liked_merchants": liked_merchants,
        "liked_processes": liked_processes,
        "liked_origins": liked_origins,
        "prefers_single_origin": prefers_single_origin,
    }


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
    name = product.name.lower()
    if product.is_espresso_recommended:
        score += 0.15
        reasons.append("merchant signals espresso suitability")
    if "washed" in process:
        score += 0.12
        reasons.append("washed process tends to suit clean espresso well")
    if "honey" in process:
        score += 0.08
    if "anaerobic" in process:
        score += 0.05
        reasons.append("cleaner anaerobic lots can still work well here")
    if "blend" in name:
        score -= 0.04
    if "subscription" in name or "sample box" in name:
        score -= 0.18
        reasons.append("subscription formats are weaker one-off recommendations")
    if shot_style == "turbo" and "washed" in process:
        score += 0.08
        reasons.append("turbo mode prefers clean, high-clarity coffees")
    if shot_style == "cremina_49mm":
        if "washed" in process:
            score += 0.08
            reasons.append("lever shots benefit from stable washed coffees")
        if "anaerobic" in process:
            score -= 0.08
            reasons.append("cremina mode penalizes funkier process risk")
    if shot_style == "experimental":
        if "anaerobic" in process or "natural" in process:
            score += 0.08
            reasons.append("experimental mode welcomes bolder process profiles")
    if "blackberry" in notes or "citrus" in notes or "floral" in notes:
        score += 0.04
    return min(score, 1.0), reasons


def _history_fit(product: Product, merchant: Merchant, prefs: dict, allow_decaf: bool) -> tuple[float, list[str]]:
    score = 0.5
    reasons: list[str] = []
    if merchant.id in prefs["liked_merchants"]:
        score += 0.18
        reasons.append("matches a merchant with strong purchase history")
    if product.process_text and any(process in product.process_text.lower() for process in prefs["liked_processes"]):
        score += 0.08
        reasons.append("matches a process you have rated well")
    if product.origin_text and any(origin in product.origin_text.lower() for origin in prefs["liked_origins"]):
        score += 0.08
        reasons.append("matches an origin you have rated well")
    if prefs["prefers_single_origin"] and product.is_single_origin:
        score += 0.08
        reasons.append("single origin fits your purchase history")
    elif prefs["prefers_single_origin"] and not product.is_single_origin:
        score -= 0.08
        reasons.append("blend or mixed offering is weaker for your history")
    if "decaf" in product.name.lower() and not allow_decaf:
        score -= 0.35
        reasons.append("decaf is penalized by default")
    if "subscription" in product.name.lower() or "sample box" in product.name.lower():
        score -= 0.18
        reasons.append("subscriptions and sample boxes are downranked")
    return max(0.0, min(score, 1.0)), reasons


def _promo_bonus(session: Session, merchant_id: int) -> tuple[float, list[str]]:
    promos = session.scalars(
        select(PromoSnapshot)
        .where(PromoSnapshot.merchant_id == merchant_id)
        .order_by(PromoSnapshot.observed_at.desc())
        .limit(3)
    ).all()
    bonus = 0.0
    reasons: list[str] = []
    for promo in promos:
        if promo.promo_type == "percent_off":
            bonus = max(bonus, 0.08)
            reasons.append("merchant has an active percent-off promo")
        elif promo.promo_type in {"free_shipping", "free_shipping_variant"}:
            bonus = max(bonus, 0.05)
            reasons.append("merchant has a shipping-related promo")
        elif promo.promo_type == "dollar_off":
            bonus = max(bonus, 0.06)
            reasons.append("merchant has a dollar-off promo")
        elif promo.promo_type == "subscription_discount":
            bonus = max(bonus, 0.04)
            reasons.append("merchant advertises subscription savings")
    return bonus, reasons


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
    prefs = _preference_profile(session)
    products = session.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())).all()

    for product in products:
        merchant = product.merchant
        merchant_score = _merchant_score_with_shot_style(merchant, request.shot_style)
        shipping_policy = _latest_shipping_policy(session, merchant.id)
        history_score, history_reasons = _history_fit(product, merchant, prefs, request.allow_decaf)
        promo_bonus, promo_reasons = _promo_bonus(session, merchant.id)
        for variant in product.variants:
            if not variant.is_whole_bean:
                continue
            format_haystack = f"{product.name} {variant.label}".lower()
            if any(term in format_haystack for term in ["instant", "pod", "capsule", "packet", "packets"]):
                continue
            offer = _latest_offer(session, variant.id)
            if offer is None or not offer.is_available:
                continue

            quantity_score = _quantity_score(variant.weight_grams, request.quantity_mode, request.bulk_allowed)
            espresso_score, espresso_reasons = _espresso_fit(product, request.shot_style)
            deal_score, landed, deal_reasons = _deal_score(offer, variant, shipping_policy)
            freshness_score = merchant.quality_profile.freshness_transparency_score if merchant.quality_profile else 0.5

            total = (
                merchant_score * 0.24
                + quantity_score * 0.18
                + espresso_score * 0.20
                + deal_score * 0.12
                + freshness_score * 0.08
                + history_score * 0.18
                + promo_bonus
            )

            rationale = [
                f"merchant trust score {merchant_score:.2f}",
                f"quantity fit score {quantity_score:.2f}",
                f"deal score {deal_score:.2f}",
                f"history fit score {history_score:.2f}",
            ]
            rationale.extend(espresso_reasons[:2])
            rationale.extend(deal_reasons[:2])
            rationale.extend(history_reasons[:2])
            rationale.extend(promo_reasons[:1])

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
    selected: list[RecommendationCandidate] = []
    per_merchant_counts: dict[str, int] = {}
    for candidate in candidates:
        count = per_merchant_counts.get(candidate.merchant_name, 0)
        if count >= 2:
            continue
        per_merchant_counts[candidate.merchant_name] = count + 1
        selected.append(candidate)
        if len(selected) >= 5:
            break
    return selected


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
