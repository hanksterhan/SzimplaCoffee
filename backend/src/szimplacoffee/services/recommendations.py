from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import median
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    Merchant,
    MerchantPromo,
    OfferSnapshot,
    Product,
    ProductVariant,
    PurchaseHistory,
    RecommendationRun,
    ShippingPolicy,
    VariantDealFact,
)
from .discovery import meets_buying_threshold


QuantityMode = Literal["12-18 oz", "2 lb", "5 lb", "any"]
ShotStyle = Literal["modern_58mm", "cremina_49mm", "turbo", "experimental"]

# SC-54: Score threshold below which the system recommends waiting
WAIT_SCORE_THRESHOLD = 0.30


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
    image_url: str
    weight_grams: int | None
    landed_price_cents: int
    landed_price_per_oz_cents: int | None
    best_promo_label: str | None
    discounted_landed_price_cents: int | None
    score: float
    pros: list[str]


@dataclass
class BiggestSaleCandidate:
    merchant_name: str
    product_name: str
    variant_label: str
    product_url: str
    image_url: str
    weight_grams: int | None
    current_price_cents: int
    landed_price_cents: int
    landed_price_per_oz_cents: int | None
    compare_at_discount_percent: float
    price_drop_7d_percent: float
    price_drop_30d_percent: float
    historical_low_cents: int
    best_promo_label: str | None
    discounted_landed_price_cents: int | None
    score: float
    reasons: list[str]


def _latest_offer(session: Session, variant_id: int) -> OfferSnapshot | None:
    return session.scalar(
        select(OfferSnapshot)
        .where(OfferSnapshot.variant_id == variant_id)
        .order_by(OfferSnapshot.observed_at.desc())
        .limit(1)
    )


def _offer_history(session: Session, variant_id: int) -> list[OfferSnapshot]:
    return session.scalars(
        select(OfferSnapshot)
        .where(OfferSnapshot.variant_id == variant_id)
        .order_by(OfferSnapshot.observed_at.desc())
    ).all()


def _latest_shipping_policy(session: Session, merchant_id: int) -> ShippingPolicy | None:
    return session.scalar(
        select(ShippingPolicy)
        .where(ShippingPolicy.merchant_id == merchant_id)
        .order_by(ShippingPolicy.observed_at.desc())
        .limit(1)
    )


def _median_price(prices: list[int]) -> int | None:
    if not prices:
        return None
    return int(round(median(prices)))


def _historical_window_prices(
    offers: list[OfferSnapshot],
    *,
    reference_offer: OfferSnapshot,
    days: int,
) -> list[int]:
    window_start = reference_offer.observed_at - timedelta(days=days)
    return [
        offer.price_cents
        for offer in offers
        if window_start <= offer.observed_at < reference_offer.observed_at
    ]


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
        select(MerchantPromo)
        .where(MerchantPromo.merchant_id == merchant_id, MerchantPromo.is_active.is_(True))
        .order_by(MerchantPromo.estimated_value_cents.desc().nullslast(), MerchantPromo.last_seen_at.desc())
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


def _discounted_price_cents(landed_price_cents: int, offer: OfferSnapshot, promo: MerchantPromo) -> tuple[int | None, str | None]:
    if promo.promo_type in {"percent_off", "subscription_discount"} and promo.estimated_value_cents:
        percent = promo.estimated_value_cents / 100
        discounted = int(round(landed_price_cents * (1 - (percent / 100))))
        label = f"{percent:.0f}% off" if promo.promo_type == "percent_off" else f"{percent:.0f}% off with subscription"
        return max(discounted, 0), label
    if promo.promo_type == "dollar_off" and promo.estimated_value_cents:
        discounted = max(landed_price_cents - promo.estimated_value_cents, 0)
        return discounted, promo.title
    if promo.promo_type in {"free_shipping", "free_shipping_variant"} and landed_price_cents > offer.price_cents:
        label = "Free shipping"
        if promo.promo_type == "free_shipping":
            label = "Free shipping on qualifying order"
        return offer.price_cents, label
    return None, None


def _best_active_promo(session: Session, merchant_id: int, landed_price_cents: int, offer: OfferSnapshot) -> tuple[str | None, int | None]:
    promos = session.scalars(
        select(MerchantPromo)
        .where(MerchantPromo.merchant_id == merchant_id, MerchantPromo.is_active.is_(True))
        .order_by(MerchantPromo.estimated_value_cents.desc().nullslast(), MerchantPromo.last_seen_at.desc())
    ).all()
    best_label: str | None = None
    best_price: int | None = None
    best_savings = 0
    for promo in promos:
        discounted, label = _discounted_price_cents(landed_price_cents, offer, promo)
        if discounted is None or label is None:
            continue
        savings = landed_price_cents - discounted
        if savings > best_savings:
            best_savings = savings
            best_label = label
            best_price = discounted
    return best_label, best_price


def _landed_price_cents(offer: OfferSnapshot, shipping_policy: ShippingPolicy | None) -> int:
    if shipping_policy and shipping_policy.free_shipping_threshold_cents and offer.price_cents >= shipping_policy.free_shipping_threshold_cents:
        return offer.price_cents
    return offer.price_cents + 800


def _price_per_oz_cents(price_cents: int, weight_grams: int | None) -> int | None:
    if not weight_grams:
        return None
    ounces = weight_grams / 28.3495
    if ounces <= 0:
        return None
    return int(round(price_cents / ounces))


def _historical_discount_percent(baseline_cents: int | None, current_price_cents: int) -> float:
    if not baseline_cents or baseline_cents <= 0 or current_price_cents >= baseline_cents:
        return 0.0
    return round(((baseline_cents - current_price_cents) / baseline_cents) * 100, 2)


def _materialize_variant_deal_fact(
    session: Session,
    variant: ProductVariant,
) -> VariantDealFact | None:
    offers = _offer_history(session, variant.id)
    if not offers:
        return None

    latest_offer = offers[0]
    prices = [offer.price_cents for offer in offers]
    baseline_7d = _median_price(_historical_window_prices(offers, reference_offer=latest_offer, days=7))
    baseline_30d = _median_price(_historical_window_prices(offers, reference_offer=latest_offer, days=30))
    compare_at_discount_percent = 0.0
    if latest_offer.compare_at_price_cents and latest_offer.compare_at_price_cents > latest_offer.price_cents:
        compare_at_discount_percent = round(
            ((latest_offer.compare_at_price_cents - latest_offer.price_cents) / latest_offer.compare_at_price_cents) * 100,
            2,
        )

    fact = session.scalar(
        select(VariantDealFact).where(VariantDealFact.variant_id == variant.id)
    )
    if fact is None:
        fact = VariantDealFact(variant_id=variant.id)
        session.add(fact)

    fact.offer_count = len(offers)
    fact.distinct_offer_days = len({offer.observed_at.date() for offer in offers})
    fact.current_price_cents = latest_offer.price_cents
    fact.baseline_7d_cents = baseline_7d
    fact.baseline_30d_cents = baseline_30d
    fact.historical_low_cents = min(prices)
    fact.historical_high_cents = max(prices)
    fact.compare_at_discount_percent = compare_at_discount_percent
    fact.price_drop_7d_percent = _historical_discount_percent(baseline_7d, latest_offer.price_cents)
    fact.price_drop_30d_percent = _historical_discount_percent(baseline_30d, latest_offer.price_cents)
    return fact


def materialize_variant_deal_facts(session: Session) -> dict[int, VariantDealFact]:
    facts: dict[int, VariantDealFact] = {}
    variants = session.scalars(
        select(ProductVariant)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(Product.is_active.is_(True))
    ).all()
    for variant in variants:
        fact = _materialize_variant_deal_fact(session, variant)
        if fact is not None:
            facts[variant.id] = fact
    session.flush()
    return facts


def _catalog_price_per_oz_baseline_cents(session: Session) -> int | None:
    price_points: list[int] = []
    variants = session.scalars(
        select(ProductVariant)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(Product.is_active.is_(True), ProductVariant.is_whole_bean.is_(True), ProductVariant.is_available.is_(True))
    ).all()
    for variant in variants:
        latest_offer = _latest_offer(session, variant.id)
        if latest_offer is None or not latest_offer.is_available:
            continue
        shipping_policy = _latest_shipping_policy(session, variant.product.merchant_id)
        landed_price = _landed_price_cents(latest_offer, shipping_policy)
        price_per_oz = _price_per_oz_cents(landed_price, variant.weight_grams)
        if price_per_oz is not None:
            price_points.append(price_per_oz)
    return _median_price(price_points)


def _deal_score(
    fact: VariantDealFact,
    variant: ProductVariant,
    offer: OfferSnapshot,
    shipping_policy: ShippingPolicy | None,
    *,
    promo_bonus: float,
    promo_reasons: list[str],
    category_price_per_oz_baseline_cents: int | None,
) -> tuple[float, int, list[str]]:
    landed = _landed_price_cents(offer, shipping_policy)
    landed_price_per_oz_cents = _price_per_oz_cents(landed, variant.weight_grams)
    reasons: list[str] = []

    if fact.price_drop_7d_percent >= 5:
        reasons.append(f"current price is {fact.price_drop_7d_percent:.0f}% below the 7-day median")
    if fact.price_drop_30d_percent >= 5:
        reasons.append(f"current price is {fact.price_drop_30d_percent:.0f}% below the 30-day median")
    if fact.compare_at_discount_percent >= 5:
        reasons.append(f"current price is {fact.compare_at_discount_percent:.0f}% below compare-at")
    if (
        landed_price_per_oz_cents is not None
        and category_price_per_oz_baseline_cents is not None
        and landed_price_per_oz_cents <= category_price_per_oz_baseline_cents
    ):
        reasons.append("landed price per ounce is at or below the current catalog baseline")
    if fact.current_price_cents <= fact.historical_low_cents:
        reasons.append("matches the historical low price for this variant")
    if shipping_policy and shipping_policy.free_shipping_threshold_cents and offer.price_cents >= shipping_policy.free_shipping_threshold_cents:
        reasons.append("qualifies for free shipping")
    if promo_reasons:
        reasons.append(promo_reasons[0])

    historical_signal = max(
        fact.compare_at_discount_percent / 30,
        fact.price_drop_7d_percent / 25,
        fact.price_drop_30d_percent / 30,
        1.0 if fact.current_price_cents <= fact.historical_low_cents else 0.0,
    )
    historical_score = max(0.2, min(historical_signal, 1.0))

    price_per_oz_score = 0.45
    if landed_price_per_oz_cents is not None and category_price_per_oz_baseline_cents is not None and category_price_per_oz_baseline_cents > 0:
        ratio = landed_price_per_oz_cents / category_price_per_oz_baseline_cents
        if ratio <= 0.85:
            price_per_oz_score = 1.0
        elif ratio <= 1.0:
            price_per_oz_score = 0.8
        elif ratio <= 1.1:
            price_per_oz_score = 0.6
        else:
            price_per_oz_score = 0.35

    total = min(1.0, (historical_score * 0.7) + (price_per_oz_score * 0.2) + promo_bonus)
    return total, landed, reasons


def _build_pros(
    merchant_score: float,
    quantity_score: float,
    deal_score: float,
    espresso_reasons: list[str],
    deal_reasons: list[str],
    history_reasons: list[str],
    promo_label: str | None,
) -> list[str]:
    pros: list[str] = []
    if merchant_score >= 0.8:
        pros.append("Trusted merchant with a strong quality signal")
    if quantity_score >= 0.95:
        pros.append("Bag size matches your current buying window")
    if espresso_reasons:
        pros.append(espresso_reasons[0][:1].upper() + espresso_reasons[0][1:])
    if deal_score >= 0.8:
        pros.append("Strong delivered value for the amount of coffee")
    elif deal_reasons:
        pros.append(deal_reasons[0][:1].upper() + deal_reasons[0][1:])
    if promo_label:
        pros.append(f"Merchant offer available: {promo_label.lower()}")
    if history_reasons:
        first = history_reasons[0]
        if "merchant" in first or "history" in first:
            pros.append("Matches merchants and coffees you have liked before")
        else:
            pros.append(first[:1].upper() + first[1:])

    deduped: list[str] = []
    seen: set[str] = set()
    for pro in pros:
        key = pro.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pro)
        if len(deduped) >= 4:
            break
    return deduped


def build_biggest_sales(session: Session, limit: int = 10) -> list[BiggestSaleCandidate]:
    fact_by_variant = materialize_variant_deal_facts(session)
    category_baseline = _catalog_price_per_oz_baseline_cents(session)
    candidates: list[BiggestSaleCandidate] = []

    products = session.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())).all()
    for product in products:
        merchant = product.merchant
        # SC-53: exclude merchants below buying threshold
        if not meets_buying_threshold(merchant):
            continue
        merchant_quality = _merchant_quality_score(merchant)
        if merchant_quality < 0.65:
            continue

        shipping_policy = _latest_shipping_policy(session, merchant.id)
        promo_bonus, promo_reasons = _promo_bonus(session, merchant.id)
        for variant in product.variants:
            if not variant.is_whole_bean or not variant.is_available:
                continue
            offer = _latest_offer(session, variant.id)
            if offer is None or not offer.is_available:
                continue
            fact = fact_by_variant.get(variant.id)
            if fact is None:
                continue

            deal_score, landed, reasons = _deal_score(
                fact,
                variant,
                offer,
                shipping_policy,
                promo_bonus=promo_bonus,
                promo_reasons=promo_reasons,
                category_price_per_oz_baseline_cents=category_baseline,
            )
            score = round((deal_score * 0.72) + (merchant_quality * 0.28), 4)
            if score < 0.58:
                continue

            best_promo_label, discounted_landed_price_cents = _best_active_promo(session, merchant.id, landed, offer)
            candidates.append(
                BiggestSaleCandidate(
                    merchant_name=merchant.name,
                    product_name=product.name,
                    variant_label=variant.label,
                    product_url=product.product_url,
                    image_url=product.image_url,
                    weight_grams=variant.weight_grams,
                    current_price_cents=offer.price_cents,
                    landed_price_cents=landed,
                    landed_price_per_oz_cents=_price_per_oz_cents(landed, variant.weight_grams),
                    compare_at_discount_percent=fact.compare_at_discount_percent,
                    price_drop_7d_percent=fact.price_drop_7d_percent,
                    price_drop_30d_percent=fact.price_drop_30d_percent,
                    historical_low_cents=fact.historical_low_cents,
                    best_promo_label=best_promo_label,
                    discounted_landed_price_cents=discounted_landed_price_cents,
                    score=score,
                    reasons=reasons[:4],
                )
            )

    candidates.sort(key=lambda item: item.score, reverse=True)
    return candidates[:limit]


def build_recommendations(session: Session, request: RecommendationRequest) -> list[RecommendationCandidate]:
    candidates: list[RecommendationCandidate] = []
    prefs = _preference_profile(session)
    fact_by_variant = materialize_variant_deal_facts(session)
    category_baseline = _catalog_price_per_oz_baseline_cents(session)
    products = session.scalars(select(Product).where(Product.is_active.is_(True)).order_by(Product.name.asc())).all()

    for product in products:
        merchant = product.merchant
        # SC-53: exclude merchants below buying threshold from recommendations
        if not meets_buying_threshold(merchant):
            continue
        merchant_score = _merchant_score_with_shot_style(merchant, request.shot_style)
        shipping_policy = _latest_shipping_policy(session, merchant.id)
        history_score, history_reasons = _history_fit(product, merchant, prefs, request.allow_decaf)
        promo_bonus, promo_reasons = _promo_bonus(session, merchant.id)
        for variant in product.variants:
            if not variant.is_whole_bean:
                continue
            if not variant.is_available:
                continue
            format_haystack = f"{product.name} {variant.label}".lower()
            if any(term in format_haystack for term in ["instant", "pod", "capsule", "packet", "packets"]):
                continue
            offer = _latest_offer(session, variant.id)
            if offer is None or not offer.is_available:
                continue
            fact = fact_by_variant.get(variant.id)
            if fact is None:
                continue

            quantity_score = _quantity_score(variant.weight_grams, request.quantity_mode, request.bulk_allowed)
            espresso_score, espresso_reasons = _espresso_fit(product, request.shot_style)
            deal_score, landed, deal_reasons = _deal_score(
                fact,
                variant,
                offer,
                shipping_policy,
                promo_bonus=promo_bonus,
                promo_reasons=promo_reasons,
                category_price_per_oz_baseline_cents=category_baseline,
            )
            best_promo_label, discounted_landed_price_cents = _best_active_promo(session, merchant.id, landed, offer)
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

            pros = _build_pros(
                merchant_score,
                quantity_score,
                deal_score,
                espresso_reasons,
                deal_reasons,
                history_reasons,
                best_promo_label,
            )

            candidates.append(
                RecommendationCandidate(
                    merchant_name=merchant.name,
                    product_name=product.name,
                    variant_label=variant.label,
                    product_url=product.product_url,
                    image_url=product.image_url,
                    weight_grams=variant.weight_grams,
                    landed_price_cents=landed,
                    landed_price_per_oz_cents=_price_per_oz_cents(landed, variant.weight_grams),
                    best_promo_label=best_promo_label,
                    discounted_landed_price_cents=discounted_landed_price_cents,
                    score=round(total, 4),
                    pros=pros,
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


def build_wait_assessment(candidates: list[RecommendationCandidate], no_candidates: bool = False) -> tuple[bool, str | None]:
    """SC-54: Determine if the system should recommend waiting, and why.

    Returns (wait_recommendation, wait_rationale).
    """
    if no_candidates:
        return True, "No coffee meets the current filters — try broadening your criteria or check back after the next crawl cycle."
    if not candidates:
        return True, "No matching options found right now."
    top_score = candidates[0].score
    if top_score < WAIT_SCORE_THRESHOLD:
        return True, f"The best current option scores {top_score:.0%} — below the quality threshold. Check back after merchants are refreshed."
    return False, None


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
