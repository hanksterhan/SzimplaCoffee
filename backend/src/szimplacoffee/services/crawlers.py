from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import html
import json
import re
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    CrawlRun,
    Merchant,
    MerchantFieldPattern,
    MerchantPromo,
    OfferSnapshot,
    Product,
    ProductMetadataOverride,
    ProductVariant,
    PromoSnapshot,
    ShippingPolicy,
)
from .coffee_parser import parse_coffee_metadata

# ---------------------------------------------------------------------------
# Crawl strategy layer constants
# The crawl pipeline tries layers in order: feed → structured → dom → agentic
# Each dimension (catalog, promo, shipping, metadata) tracks its best layer.
# ---------------------------------------------------------------------------
STRATEGY_FEED = "feed"           # JSON API / product feed (highest fidelity)
STRATEGY_STRUCTURED = "structured"  # Structured data: JSON-LD, microdata
STRATEGY_DOM = "dom"             # DOM extraction (WooCommerce variations form, etc.)
STRATEGY_AGENTIC = "agentic"     # Heuristic crawl across product detail pages
STRATEGY_NONE = "none"           # Not attempted or yielded no useful data

USER_AGENT = "SzimplaCoffeeBot/0.1 (+local-first research utility)"
_STRUCTURED_METADATA_FIELDS = (
    "origin_text",
    "process_text",
    "variety_text",
    "roast_cues",
    "tasting_notes_text",
)
_OVERRIDABLE_METADATA_FIELDS = (
    "origin_text",
    "origin_country",
    "origin_region",
    "process_text",
    "process_family",
    "variety_text",
    "roast_cues",
    "roast_level",
    "tasting_notes_text",
    "is_single_origin",
    "is_espresso_recommended",
)


@dataclass
class CrawlSummary:
    adapter_name: str
    records_written: int
    confidence: float
    # Strategy layer used for each extraction dimension
    catalog_strategy: str = STRATEGY_NONE
    promo_strategy: str = STRATEGY_NONE
    shipping_strategy: str = STRATEGY_NONE
    metadata_strategy: str = STRATEGY_NONE

    @property
    def crawl_quality_score(self) -> float:
        """Derive a [0–1] quality score from strategy layers and confidence."""
        layer_scores = {
            STRATEGY_FEED: 1.0,
            STRATEGY_STRUCTURED: 0.85,
            STRATEGY_DOM: 0.70,
            STRATEGY_AGENTIC: 0.55,
            STRATEGY_NONE: 0.0,
        }
        catalog_score = layer_scores.get(self.catalog_strategy, 0.0)
        # Weight: catalog 50%, metadata 30%, promo 10%, shipping 10%
        metadata_score = layer_scores.get(self.metadata_strategy, 0.0)
        promo_score = layer_scores.get(self.promo_strategy, 0.0)
        shipping_score = layer_scores.get(self.shipping_strategy, 0.0)
        composite = (
            0.50 * catalog_score
            + 0.30 * metadata_score
            + 0.10 * promo_score
            + 0.10 * shipping_score
        )
        # Blend with confidence (confidence comes from adapter fidelity)
        return round(0.60 * composite + 0.40 * self.confidence, 3)


@dataclass
class PromoCandidate:
    promo_key: str
    promo_type: str
    title: str
    details: str
    source_urls: set[str]
    code: str | None
    estimated_value_cents: int | None
    confidence: float


@dataclass
class WooPageContext:
    variation_rows: list[dict]
    summary_text: str


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _clean_text(markup: str | None) -> str:
    if not markup:
        return ""
    text = BeautifulSoup(markup, "lxml").get_text("\n", strip=True)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _normalize_product_name(name: str) -> str:
    normalized = re.sub(r"(?i)<br\s*/?>", " • ", name)
    normalized = html.unescape(normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _strip_query_fragment(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def _site_root(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def _normalize_asset_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    return url


def _shopify_catalog_urls(homepage_url: str) -> list[str]:
    root_url = _site_root(homepage_url)
    landing_url = _strip_query_fragment(homepage_url)
    path = urlparse(landing_url).path.rstrip("/")
    candidates: list[str] = []
    if path.startswith("/collections/"):
        candidates.append(f"{root_url}{path}/products.json?limit=250")
    elif path:
        candidates.append(f"{landing_url}/products.json?limit=250")
    candidates.append(f"{root_url}/products.json?limit=250")

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped


def _extract_field(text: str, label: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(label)}\s*:?\s*(.+)$", re.IGNORECASE)
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            return match.group(1).strip()
    return ""


def _extract_free_shipping_threshold(text: str) -> int | None:
    match = re.search(r"free shipping[^$]*\$(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1)) * 100
    return None


def _extract_code(text: str) -> str | None:
    match = re.search(r"(?i:(?:use\s+code|promo\s+code|code)\s*[:\-]?\s*)([A-Z0-9]{4,16})\b", text)
    if match:
        return match.group(1).upper()
    return None


def _extract_discount_percent(text: str) -> int | None:
    match = re.search(r"(\d{1,2})\s*%+\s*(?:off|discount)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_discount_dollars(text: str) -> int | None:
    match = re.search(r"save\s*\$?(\d+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if match:
        return int(round(float(match.group(1)) * 100))
    return None


def _extract_subscription_discount(text: str) -> int | None:
    match = re.search(r"(?:subscribe(?:\s*&\s*save)?|subscription)[^\d]{0,30}(\d{1,2})\s*%", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _parse_price_to_cents(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    normalized = str(value).replace("$", "").replace(",", "").strip()
    if normalized.isdigit():
        if "." not in normalized:
            return int(normalized)
    try:
        return int(round(float(normalized) * 100))
    except ValueError:
        return None


def _parse_weight_grams(label: str) -> int | None:
    lowered = label.lower()
    pack_match = re.search(
        r"(?:(\d+|one|two|three|four|five|six)\s*x\s*(\d+(?:\.\d+)?)\s*oz)|(?:(\d+|one|two|three|four|five|six)\s+(\d+(?:\.\d+)?)\s*oz\s+bags?)",
        lowered,
    )
    if pack_match:
        count_token = pack_match.group(1) or pack_match.group(3)
        amount_token = pack_match.group(2) or pack_match.group(4)
        count_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
        count = count_map.get(count_token, int(count_token) if count_token.isdigit() else 1)
        return int(round(count * float(amount_token) * 28.3495))
    oz_match = re.search(r"(\d+(?:\.\d+)?)\s*oz", lowered)
    if oz_match:
        return int(round(float(oz_match.group(1)) * 28.3495))
    lb_match = re.search(r"(\d+(?:\.\d+)?)\s*lb", lowered)
    if lb_match:
        return int(round(float(lb_match.group(1)) * 453.592))
    g_match = re.search(r"(\d+(?:\.\d+)?)\s*g", lowered)
    if g_match:
        return int(round(float(g_match.group(1))))
    return None


def _normalize_single_origin_flag(name: str, tags: Iterable[str], text: str, categories: Iterable[str] | None = None) -> bool:
    haystack = " ".join([name, text, *tags, *(categories or [])]).lower()
    if any(term in haystack for term in ["blend", "subscription", "sample box", "sampler"]):
        return False
    return "single origin" in haystack


def _extract_tasting_notes(text: str) -> str:
    for label in ["Tastes Like", "Notes", "Flavor Notes", "Tasting Notes"]:
        value = _extract_field(text, label)
        if value:
            return value
    prose_match = re.search(r"(?:notes of|flavors? of)\s+([^.;]+)", text, re.IGNORECASE)
    if prose_match:
        return prose_match.group(1).strip()
    return ""


def _infer_origin_from_text(name: str, text: str) -> str:
    known_origins = [
        "Ethiopia",
        "Kenya",
        "Colombia",
        "El Salvador",
        "Guatemala",
        "Peru",
        "Brazil",
        "Burundi",
        "Rwanda",
        "Costa Rica",
        "Honduras",
        "Panama",
        "Mexico",
        "Ecuador",
    ]
    haystack = f"{name}\n{text}"
    for origin in known_origins:
        if origin.lower() in haystack.lower():
            return origin
    return ""


def _extract_intro_tokens(text: str) -> list[str]:
    for line in text.splitlines():
        if line.count("|") >= 2:
            return [token.strip() for token in line.split("|") if token.strip()]
    return []


def _extract_process_from_text(name: str, text: str) -> str:
    for candidate in _extract_intro_tokens(text) + [name]:
        match = re.search(r"(washed|natural|honey|anaerobic(?: natural| washed)?|wet hulled)", candidate, re.IGNORECASE)
        if match:
            return match.group(1).title()
    return ""


def _extract_variety_from_text(name: str, text: str) -> str:
    for token in _extract_intro_tokens(text):
        lowered = token.lower()
        if "masl" in lowered:
            continue
        if re.search(r"(washed|natural|honey|anaerobic|wet hulled)", lowered):
            continue
        if any(char.isdigit() for char in token) or "%" in token or any(term in lowered for term in ["geisha", "bourbon", "caturra", "castillo", "bernardina", "sl-", "ruiru", "typica"]):
            return token
    return ""


def _merge_origin_and_site(origin: str, site_token: str) -> str:
    if not site_token:
        return origin
    if not origin:
        return site_token
    if site_token.lower() == origin.lower():
        return origin
    if site_token.lower() in origin.lower():
        return origin
    return f"{origin} · {site_token}"


def _is_coffee_product(name: str, product_type: str = "", tags: Iterable[str] | None = None, categories: Iterable[str] | None = None) -> bool:
    haystacks = [name, product_type]
    if tags:
        haystacks.extend(tags)
    if categories:
        haystacks.extend(categories)
    text = " ".join(haystacks).lower()
    negative_keywords = [
        "mug",
        "cup",
        "kettle",
        "grinder",
        "mill",
        "dripper",
        "brew guide",
        "sticker",
        "hat",
        "shirt",
        "hoodie",
        "chocolate",
        "barista oat milk",
        "paper",
        "gift card",
        "ground for brew",
        "ground coffee",
        "espresso machine",
        "instant",
        "pod",
        "pods",
        "capsule",
        "capsules",
        "packet",
        "packets",
        "machine",
        "maker",
        "burr",
        "replacement part",
        "tamper",
        "portafilter",
        "basket",
        "knock box",
        "scale",
        "carafe",
        "server",
        "tumbler",
        "book",
        "course",
        "class",
    ]
    if any(keyword in text for keyword in negative_keywords):
        return False
    return any(
        needle in text
        for needle in [
            "coffee",
            "espresso",
            "single origin",
            "blend",
            "subscription",
            "filter",
        ]
    )


def _enrich_payload_with_parser(payload: dict, name: str, description: str) -> dict:
    """Run the coffee metadata parser and fill payload gaps.

    The parser output is only applied when the crawler's heuristics left a
    field empty, so hand-structured descriptions (Origin: X labels) still
    take priority.
    """
    structured_seeded = any(payload.get(field) for field in _STRUCTURED_METADATA_FIELDS)
    parsed = parse_coffee_metadata(name, description)
    if not payload.get("origin_text") and parsed.origin_text:
        payload["origin_text"] = parsed.origin_text
    if not payload.get("process_text") and parsed.process_text:
        payload["process_text"] = parsed.process_text
    if not payload.get("variety_text") and parsed.variety_text:
        payload["variety_text"] = parsed.variety_text
    if not payload.get("roast_cues") and parsed.roast_cues:
        payload["roast_cues"] = parsed.roast_cues
    if not payload.get("tasting_notes_text") and parsed.tasting_notes_text:
        payload["tasting_notes_text"] = parsed.tasting_notes_text
    if not payload.get("origin_country") and parsed.origin_country:
        payload["origin_country"] = parsed.origin_country
    if not payload.get("origin_region") and parsed.origin_region:
        payload["origin_region"] = parsed.origin_region
    if payload.get("process_family") in (None, "", "unknown") and parsed.process_family != "unknown":
        payload["process_family"] = parsed.process_family
    if payload.get("roast_level") in (None, "", "unknown") and parsed.roast_level != "unknown":
        payload["roast_level"] = parsed.roast_level
    # Flags: parser wins if crawler left defaults
    if not payload.get("is_single_origin"):
        payload["is_single_origin"] = parsed.is_single_origin
    if not payload.get("is_espresso_recommended"):
        payload["is_espresso_recommended"] = parsed.is_espresso_recommended
    normalized_found = any(
        payload.get(field)
        for field in ("origin_country", "origin_region", "process_family", "roast_level")
    )
    if normalized_found:
        source = "structured" if structured_seeded else parsed.metadata_source
        payload["metadata_source"] = payload.get("metadata_source") or source
        payload["metadata_confidence"] = max(
            float(payload.get("metadata_confidence") or 0.0),
            0.85 if source == "structured" else parsed.confidence,
        )
    return payload


def _metadata_haystack(name: str, description: str, payload: dict) -> str:
    return "\n".join(
        str(part)
        for part in [
            name,
            description,
            payload.get("origin_text", ""),
            payload.get("process_text", ""),
            payload.get("variety_text", ""),
            payload.get("roast_cues", ""),
            payload.get("tasting_notes_text", ""),
        ]
        if part
    )


def _coerce_override_value(field_name: str, value: str) -> str | bool | None:
    if field_name in {"is_single_origin", "is_espresso_recommended"}:
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
        return None
    return value.strip()


def _apply_metadata_rule(payload: dict, field_name: str, value: str, confidence: float) -> bool:
    if field_name not in _OVERRIDABLE_METADATA_FIELDS:
        return False

    coerced = _coerce_override_value(field_name, value)
    if coerced in (None, "", "unknown"):
        return False

    payload[field_name] = coerced
    payload["metadata_source"] = "override"
    payload["metadata_confidence"] = max(float(payload.get("metadata_confidence") or 0.0), confidence)
    return True


def _override_matches(
    override: ProductMetadataOverride,
    external_product_id: str,
    product_name: str,
) -> bool:
    if override.external_product_id and override.external_product_id == str(external_product_id):
        return True
    return bool(override.product_name and override.product_name.lower() == product_name.lower())


def _apply_metadata_overrides(
    session: Session,
    merchant: Merchant,
    external_product_id: str,
    payload: dict,
    name: str,
    description: str,
) -> dict:
    haystack = _metadata_haystack(name, description, payload)
    patterns = session.scalars(
        select(MerchantFieldPattern).where(
            MerchantFieldPattern.merchant_id == merchant.id,
            MerchantFieldPattern.is_active.is_(True),
        )
    ).all()
    for pattern in patterns:
        try:
            if re.search(pattern.pattern, haystack, re.IGNORECASE):
                _apply_metadata_rule(payload, pattern.field_name, pattern.normalized_value, pattern.confidence)
        except re.error:
            continue

    overrides = session.scalars(
        select(ProductMetadataOverride).where(
            ProductMetadataOverride.merchant_id == merchant.id,
            ProductMetadataOverride.is_active.is_(True),
        )
    ).all()
    for override in overrides:
        if not _override_matches(override, external_product_id, name):
            continue
        for field_name in _OVERRIDABLE_METADATA_FIELDS:
            value = getattr(override, field_name)
            if value is None or value == "" or value == "unknown":
                continue
            payload[field_name] = value
        payload["metadata_source"] = override.metadata_source or "override"
        payload["metadata_confidence"] = max(
            float(payload.get("metadata_confidence") or 0.0),
            float(override.metadata_confidence or 1.0),
        )

    return payload


def _upsert_product(session: Session, merchant: Merchant, external_product_id: str, payload: dict) -> Product:
    product = session.scalar(
        select(Product).where(
            Product.merchant_id == merchant.id,
            Product.external_product_id == str(external_product_id),
        )
    )
    if product is None:
        product = Product(
            merchant_id=merchant.id,
            external_product_id=str(external_product_id),
            name=payload["name"],
            product_url=payload["product_url"],
        )
        session.add(product)

    product.name = payload["name"]
    product.product_url = payload["product_url"]
    product.image_url = payload.get("image_url", "")
    product.origin_text = payload.get("origin_text", "")
    product.origin_country = payload.get("origin_country")
    product.origin_region = payload.get("origin_region")
    product.process_text = payload.get("process_text", "")
    product.process_family = payload.get("process_family", "unknown")
    product.variety_text = payload.get("variety_text", "")
    product.roast_cues = payload.get("roast_cues", "")
    product.roast_level = payload.get("roast_level", "unknown")
    product.tasting_notes_text = payload.get("tasting_notes_text", "")
    product.metadata_confidence = float(payload.get("metadata_confidence", 0.0) or 0.0)
    product.metadata_source = payload.get("metadata_source", "unknown")
    product.is_single_origin = payload.get("is_single_origin", False)
    product.is_espresso_recommended = payload.get("is_espresso_recommended", False)
    product.is_active = True
    product.last_seen_at = _utcnow()
    return product


def _mark_existing_products_inactive(session: Session, merchant: Merchant) -> None:
    for product in session.scalars(select(Product).where(Product.merchant_id == merchant.id)).all():
        product.is_active = False


def _mark_existing_variants_unavailable(product: Product) -> None:
    for variant in product.variants:
        variant.is_available = False


def _upsert_variant(session: Session, product: Product, external_variant_id: str, payload: dict) -> ProductVariant:
    variant = session.scalar(
        select(ProductVariant).where(
            ProductVariant.product_id == product.id,
            ProductVariant.external_variant_id == str(external_variant_id),
        )
    )
    if variant is None:
        variant = ProductVariant(
            product_id=product.id,
            external_variant_id=str(external_variant_id),
            label=payload["label"],
        )
        session.add(variant)

    variant.label = payload["label"]
    variant.weight_grams = payload.get("weight_grams")
    variant.is_available = payload.get("is_available", True)
    variant.is_whole_bean = payload.get("is_whole_bean", True)
    variant.last_seen_at = _utcnow()
    return variant


def _record_offer(session: Session, variant: ProductVariant, payload: dict) -> OfferSnapshot:
    offer = OfferSnapshot(
        variant_id=variant.id,
        observed_at=_utcnow(),
        price_cents=payload["price_cents"],
        compare_at_price_cents=payload.get("compare_at_price_cents"),
        subscription_price_cents=payload.get("subscription_price_cents"),
        is_on_sale=payload.get("is_on_sale", False),
        is_available=payload.get("is_available", True),
        source_url=payload["source_url"],
    )
    session.add(offer)
    return offer


def _normalize_promo_key(promo_type: str, estimated_value_cents: int | None, code: str | None, details: str) -> str:
    if promo_type in {"free_shipping", "free_shipping_variant"}:
        return f"free_shipping:{estimated_value_cents or 0}"
    if promo_type in {"percent_off", "dollar_off", "subscription_discount"}:
        return f"{promo_type}:{estimated_value_cents or 0}:{(code or '').lower()}"
    if promo_type == "promo_code":
        return f"{promo_type}:{(code or '').lower()}"
    detail_slug = re.sub(r"[^a-z0-9]+", "-", details.lower()).strip("-")[:48]
    return f"{promo_type}:{detail_slug}"


def _collect_promo(
    promo_buffer: dict[str, PromoCandidate],
    *,
    promo_type: str,
    title: str,
    details: str,
    source_url: str,
    confidence: float,
    code: str | None = None,
    estimated_value_cents: int | None = None,
) -> None:
    promo_key = _normalize_promo_key(promo_type, estimated_value_cents, code, details or title)
    existing = promo_buffer.get(promo_key)
    if existing:
        existing.source_urls.add(source_url)
        existing.confidence = max(existing.confidence, confidence)
        return
    promo_buffer[promo_key] = PromoCandidate(
        promo_key=promo_key,
        promo_type=promo_type,
        title=title,
        details=details,
        source_urls={source_url},
        code=code,
        estimated_value_cents=estimated_value_cents,
        confidence=confidence,
    )


def _flush_promos(session: Session, merchant: Merchant, promo_buffer: dict[str, PromoCandidate]) -> None:
    now = _utcnow()
    seen_keys = set(promo_buffer)
    existing_promos = {
        promo.promo_key: promo
        for promo in session.scalars(select(MerchantPromo).where(MerchantPromo.merchant_id == merchant.id)).all()
    }
    for promo in existing_promos.values():
        promo.is_active = False

    for promo_key, promo in promo_buffer.items():
        source_urls = "\n".join(sorted(promo.source_urls))
        current = existing_promos.get(promo_key)
        if current is None:
            current = MerchantPromo(
                merchant_id=merchant.id,
                promo_key=promo_key,
                first_seen_at=now,
            )
            session.add(current)
        current.promo_type = promo.promo_type
        current.title = promo.title
        current.details = promo.details
        current.code = promo.code
        current.estimated_value_cents = promo.estimated_value_cents
        current.source_urls = source_urls
        current.confidence = promo.confidence
        current.is_active = True
        current.last_seen_at = now

        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=now,
                promo_type=promo.promo_type,
                title=promo.title,
                details=promo.details,
                code=promo.code,
                estimated_value_cents=promo.estimated_value_cents,
                source_url=sorted(promo.source_urls)[0],
                confidence=promo.confidence,
            )
        )

    for promo_key, promo in existing_promos.items():
        if promo_key not in seen_keys:
            promo.last_seen_at = now


def _candidate_policy_urls(homepage_url: str, html: str) -> list[str]:
    root_url = _site_root(homepage_url)
    candidates = {
        f"{root_url}/pages/faq",
        f"{root_url}/pages/shipping",
        f"{root_url}/pages/subscriptions",
        f"{root_url}/policies/shipping-policy",
        f"{root_url}/policies/refund-policy",
    }
    soup = BeautifulSoup(html, "lxml")
    for link in soup.select("a[href]"):
        href = (link.get("href") or "").strip()
        text = link.get_text(" ", strip=True).lower()
        href_lower = href.lower()
        if not href_lower:
            continue
        if not (
            any(term in text for term in ["shipping", "faq", "subscription", "subscribe", "sale", "offer", "office coffee"])
            or any(
                term in href_lower
                for term in [
                    "/pages/faq",
                    "/pages/shipping",
                    "/pages/subscriptions",
                    "/policies/shipping-policy",
                    "/policies/refund-policy",
                    "/faq",
                    "/shipping",
                    "/subscribe",
                    "/subscriptions",
                ]
            )
        ):
            continue
        if any(term in href_lower for term in ["/products/", "/collections/", "/blogs/"]):
            continue
        if any(term in href_lower for term in [".jpg", ".jpeg", ".png", ".svg", ".pdf"]):
            continue
        if href.startswith("http://") or href.startswith("https://"):
            candidates.add(_strip_query_fragment(href))
        elif href.startswith("/"):
            candidates.add(_strip_query_fragment(urljoin(root_url, href)))
    return sorted(candidates)


def _record_shipping_policy(session: Session, merchant: Merchant, homepage_url: str, html: str, confidence: float) -> None:
    text = _clean_text(html)
    threshold = _extract_free_shipping_threshold(text)
    if threshold is None and "ships free" not in text.lower():
        return

    policy = ShippingPolicy(
        merchant_id=merchant.id,
        free_shipping_threshold_cents=threshold,
        shipping_notes=text[:800],
        estimated_delivery_days=3 if threshold else None,
        source_url=homepage_url,
        observed_at=_utcnow(),
        confidence=confidence,
    )
    session.add(policy)


def _record_promos(promo_buffer: dict[str, PromoCandidate], homepage_url: str, html: str, confidence: float) -> None:
    text = _clean_text(html)
    threshold = _extract_free_shipping_threshold(text)
    discount_percent = _extract_discount_percent(text)
    discount_dollars = _extract_discount_dollars(text)
    subscription_discount = _extract_subscription_discount(text)
    code = _extract_code(text)
    if threshold:
        _collect_promo(
            promo_buffer,
            promo_type="free_shipping",
            title="Free shipping",
            details=f"Free shipping on orders over ${threshold / 100:.0f}",
            source_url=homepage_url,
            estimated_value_cents=800,
            confidence=confidence,
        )
    if discount_percent:
        _collect_promo(
            promo_buffer,
            promo_type="percent_off",
            title=f"{discount_percent}% off",
            details=f"{discount_percent}% off detected on page",
            source_url=homepage_url,
            code=code,
            estimated_value_cents=discount_percent * 100,
            confidence=confidence * 0.9,
        )
    if discount_dollars:
        _collect_promo(
            promo_buffer,
            promo_type="dollar_off",
            title=f"Save ${discount_dollars / 100:.0f}",
            details="Detected dollar-off savings on page",
            source_url=homepage_url,
            code=code,
            estimated_value_cents=discount_dollars,
            confidence=confidence * 0.9,
        )
    if subscription_discount:
        _collect_promo(
            promo_buffer,
            promo_type="subscription_discount",
            title=f"{subscription_discount}% subscription savings",
            details="Detected subscription savings language",
            source_url=homepage_url,
            estimated_value_cents=subscription_discount * 100,
            confidence=confidence * 0.9,
        )
    if code and not threshold and not discount_percent and not discount_dollars:
        _collect_promo(
            promo_buffer,
            promo_type="promo_code",
            title=f"Promo code {code}",
            details="Detected promo code on page",
            source_url=homepage_url,
            code=code,
            confidence=confidence * 0.8,
        )


def _crawl_policy_pages(
    session: Session,
    merchant: Merchant,
    client: httpx.Client,
    homepage_html: str,
    confidence: float,
    promo_buffer: dict[str, PromoCandidate],
) -> None:
    for policy_url in _candidate_policy_urls(merchant.homepage_url, homepage_html):
        try:
            response = client.get(policy_url)
        except httpx.HTTPError:
            continue
        if response.status_code >= 400 or not response.text:
            continue
        _record_shipping_policy(session, merchant, policy_url, response.text, confidence * 0.9)
        _record_promos(promo_buffer, policy_url, response.text, confidence * 0.9)


def _record_shipping_variant_promo(
    promo_buffer: dict[str, PromoCandidate],
    source_url: str,
    variant_label: str,
    confidence: float,
) -> None:
    if "ships free" not in variant_label.lower():
        return
    _collect_promo(
        promo_buffer,
        promo_type="free_shipping_variant",
        title="Free shipping on bulk size",
        details=f"{variant_label} includes free shipping",
        source_url=source_url,
        estimated_value_cents=800,
        confidence=confidence * 0.85,
    )


def crawl_merchant(session: Session, merchant: Merchant, run: CrawlRun | None = None) -> CrawlSummary:
    if run is None:
        run = CrawlRun(
            merchant_id=merchant.id,
            run_type="merchant_refresh",
            adapter_name=merchant.platform_type,
            status="queued",
            confidence=0.0,
            records_written=0,
        )
        session.add(run)
        session.flush()

    try:
        run.status = "started"
        run.adapter_name = merchant.platform_type
        if merchant.platform_type == "shopify":
            summary = _crawl_shopify(session, merchant)
        elif merchant.platform_type == "woocommerce":
            summary = _crawl_woocommerce(session, merchant)
        elif merchant.platform_type in {"squarespace", "custom"}:
            summary = _crawl_generic(session, merchant)
        else:
            summary = _crawl_generic(session, merchant)

        run.finished_at = _utcnow()
        run.status = "completed"
        run.adapter_name = summary.adapter_name
        run.confidence = summary.confidence
        run.records_written = summary.records_written
        run.catalog_strategy = summary.catalog_strategy
        run.promo_strategy = summary.promo_strategy
        run.shipping_strategy = summary.shipping_strategy
        run.metadata_strategy = summary.metadata_strategy
        run.crawl_quality_score = summary.crawl_quality_score

        # SC-32: auto-update quality profile after successful crawl
        try:
            from .quality_scorer import score_merchant as _score_merchant

            _score_merchant(session, merchant)
        except Exception:
            pass  # scoring failure must not break the crawl result

        return summary
    except Exception as exc:
        run.finished_at = _utcnow()
        run.status = "failed"
        run.error_summary = str(exc)
        raise


def _crawl_shopify(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    records_written = 0
    promo_buffer: dict[str, PromoCandidate] = {}
    landing_url = _strip_query_fragment(merchant.homepage_url)
    root_url = _site_root(merchant.homepage_url)
    prefers_collection_feed = urlparse(landing_url).path.rstrip("/").startswith("/collections/")
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(landing_url)
        _record_shipping_policy(session, merchant, landing_url, homepage.text, 0.9)
        _record_promos(promo_buffer, landing_url, homepage.text, 0.9)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.9, promo_buffer)
        products: list[dict] = []
        adapter_name = "shopify"
        for catalog_url in _shopify_catalog_urls(merchant.homepage_url):
            try:
                resp = client.get(catalog_url)
                payload = resp.json()
            except (ValueError, httpx.HTTPError):
                continue
            current_products = payload.get("products", [])
            filtered_products: list[dict] = []
            for raw in current_products:
                tags = raw.get("tags", [])
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
                if _is_coffee_product(raw.get("title", ""), raw.get("product_type", ""), tags=tags):
                    filtered_products.append(raw)
            if prefers_collection_feed and "/collections/" in catalog_url and filtered_products:
                products = filtered_products
                adapter_name = "shopify_collection"
                break
            if len(filtered_products) > len(products):
                products = filtered_products
                adapter_name = "shopify_collection" if "/collections/" in catalog_url else "shopify"

        if not products:
            agentic_summary = _crawl_agentic_catalog(
                session,
                merchant,
                client,
                landing_url=landing_url,
                landing_html=homepage.text,
                confidence=0.72,
            )
            _flush_promos(session, merchant, promo_buffer)
            if agentic_summary.records_written:
                return agentic_summary
            return CrawlSummary(
                adapter_name="shopify",
                records_written=0,
                confidence=0.35,
                catalog_strategy=STRATEGY_NONE,
                promo_strategy=STRATEGY_DOM,
                shipping_strategy=STRATEGY_DOM,
                metadata_strategy=STRATEGY_NONE,
            )

        _mark_existing_products_inactive(session, merchant)

        for raw in products:
            tags = raw.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if not _is_coffee_product(raw.get("title", ""), raw.get("product_type", ""), tags=tags):
                continue

            text = _clean_text(raw.get("body_html", ""))
            product_name = _normalize_product_name(raw.get("title", "Unnamed Coffee"))
            shopify_payload = _apply_metadata_overrides(
                session,
                merchant,
                str(raw["id"]),
                _enrich_payload_with_parser(
                    {
                        "name": product_name,
                        "product_url": f"{root_url}/products/{raw.get('handle', '')}",
                        "image_url": _normalize_asset_url((raw.get("image") or {}).get("src") or ((raw.get("images") or [{}])[0].get("src") or "")),
                        "origin_text": _extract_field(text, "Origin"),
                        "process_text": _extract_field(text, "Process"),
                        "variety_text": _extract_field(text, "Variety"),
                        "roast_cues": "light" if "light" in " ".join(tags).lower() else "",
                        "tasting_notes_text": _extract_tasting_notes(text),
                        "is_single_origin": _normalize_single_origin_flag(raw.get("title", ""), tags, text),
                        "is_espresso_recommended": "espresso" in " ".join(tags).lower() or "recommended for espresso" in text.lower(),
                    },
                    product_name,
                    raw.get("body_html", ""),
                ),
                product_name,
                raw.get("body_html", ""),
            )
            product = _upsert_product(
                session,
                merchant,
                str(raw["id"]),
                shopify_payload,
            )
            session.flush()
            records_written += 1
            _mark_existing_variants_unavailable(product)

            for raw_variant in raw.get("variants", []):
                variant = _upsert_variant(
                    session,
                    product,
                    str(raw_variant["id"]),
                    {
                        "label": raw_variant.get("title", "Default"),
                        "weight_grams": raw_variant.get("grams") or _parse_weight_grams(raw_variant.get("title", "")),
                        "is_available": raw_variant.get("available", True),
                        "is_whole_bean": "ground" not in f"{raw.get('title', '')} {raw_variant.get('title', '')}".lower(),
                    },
                )
                session.flush()
                _record_offer(
                    session,
                    variant,
                    {
                        "price_cents": _parse_price_to_cents(raw_variant.get("price")) or 0,
                        "compare_at_price_cents": _parse_price_to_cents(raw_variant.get("compare_at_price")),
                        "subscription_price_cents": None,
                        "is_on_sale": bool(raw_variant.get("compare_at_price")),
                        "is_available": raw_variant.get("available", True),
                        "source_url": product.product_url,
                    },
                )
                records_written += 1

    _flush_promos(session, merchant, promo_buffer)
    return CrawlSummary(
        adapter_name=adapter_name,
        records_written=records_written,
        confidence=0.95,
        catalog_strategy=STRATEGY_FEED,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
    )


def _price_range_to_variant_prices(labels: list[str], min_cents: int | None, max_cents: int | None) -> list[int]:
    if not labels:
        return []
    if min_cents is None and max_cents is None:
        return [0 for _ in labels]
    if len(labels) == 1:
        return [min_cents or max_cents or 0]
    min_val = min_cents or max_cents or 0
    max_val = max_cents or min_cents or 0
    if len(labels) == 2:
        return [min_val, max_val]
    step = (max_val - min_val) / max(1, len(labels) - 1)
    return [int(round(min_val + step * idx)) for idx in range(len(labels))]


def _variation_name_map(attributes: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for attribute in attributes:
        if attribute.get("name", "").lower() != "size":
            continue
        for term in attribute.get("terms", []):
            display = term.get("name", "")
            slug = term.get("slug", "")
            if display:
                mapping[display.lower()] = display
            if slug:
                mapping[slug.lower()] = display or slug
            normalized_display = display.split("[", 1)[0].strip().lower()
            if normalized_display:
                mapping[normalized_display] = display
    return mapping


def _summary_context_text(soup: BeautifulSoup) -> str:
    summary = soup.select_one(".product .summary")
    if not summary:
        return ""
    return summary.get_text("\n", strip=True)


def _normalize_woo_variation_label(value: str, name_map: dict[str, str]) -> str:
    normalized = value.lower().strip()
    return name_map.get(normalized) or name_map.get(normalized.replace(" ", "")) or value


def _fetch_woocommerce_page_context(client: httpx.Client, product_url: str) -> WooPageContext:
    try:
        response = client.get(product_url)
    except httpx.HTTPError:
        return WooPageContext([], "")
    if response.status_code >= 400:
        return WooPageContext([], "")
    soup = BeautifulSoup(response.text, "lxml")
    summary_text = _summary_context_text(soup)
    form = soup.select_one("form.variations_form")
    if not form:
        return WooPageContext([], summary_text)
    raw = form.get("data-product_variations")
    if not raw:
        return WooPageContext([], summary_text)
    try:
        decoded = json.loads(html.unescape(raw))
    except json.JSONDecodeError:
        return WooPageContext([], summary_text)
    return WooPageContext(decoded if isinstance(decoded, list) else [], summary_text)


def _extract_product_links(base_url: str, html_text: str) -> list[str]:
    soup = BeautifulSoup(html_text, "lxml")
    links: list[str] = []
    seen: set[str] = set()
    for node in soup.select('a[href*="/products/"]'):
        href = (node.get("href") or "").strip()
        if "/products/" not in href:
            continue
        normalized = _strip_query_fragment(urljoin(base_url, href))
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)
    return links


def _flatten_json_nodes(payload: object) -> list[dict]:
    nodes: list[dict] = []
    if isinstance(payload, dict):
        nodes.append(payload)
        for value in payload.values():
            nodes.extend(_flatten_json_nodes(value))
    elif isinstance(payload, list):
        for item in payload:
            nodes.extend(_flatten_json_nodes(item))
    return nodes


def _extract_ld_product(soup: BeautifulSoup) -> dict:
    for node in soup.select('script[type="application/ld+json"]'):
        raw = node.get_text(strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for candidate in _flatten_json_nodes(payload):
            type_name = str(candidate.get("@type", "")).lower()
            if type_name == "product":
                return candidate
    return {}


def _extract_shopify_variant_payloads(soup: BeautifulSoup) -> list[dict]:
    for node in soup.select('script[type="application/json"]'):
        raw = node.get_text(strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(payload, list)
            and payload
            and all(isinstance(item, dict) for item in payload)
            and all("id" in item and ("price" in item or "available" in item) for item in payload)
        ):
            return payload
    return []


def _page_context_text(soup: BeautifulSoup) -> str:
    parts: list[str] = []
    for selector in [
        ".product__description",
        ".product__accordion",
        ".product__info-wrapper",
        ".product__info-container",
        ".product__info",
        "main",
    ]:
        for node in soup.select(selector):
            text = node.get_text("\n", strip=True)
            if not text:
                continue
            parts.append(text)
        if parts:
            break
    return "\n".join(parts)


def _agentic_variant_rows(ld_product: dict, variants: list[dict]) -> list[dict]:
    rows: list[dict] = []
    if variants:
        for variant in variants:
            label = variant.get("public_title") or variant.get("title") or "Default"
            rows.append(
                {
                    "external_variant_id": str(variant.get("id") or label),
                    "label": label,
                    "weight_grams": variant.get("weight") or _parse_weight_grams(label),
                    "is_available": bool(variant.get("available", True)),
                    "price_cents": _parse_price_to_cents(variant.get("price")) or 0,
                    "compare_at_price_cents": _parse_price_to_cents(variant.get("compare_at_price")),
                    "image_url": _normalize_asset_url((((variant.get("featured_image") or {}).get("src")) or "")),
                }
            )
        return rows

    offers = ld_product.get("offers") or {}
    if isinstance(offers, list):
        offer = offers[0] if offers else {}
    else:
        offer = offers if isinstance(offers, dict) else {}
    price_cents = _parse_price_to_cents(offer.get("price"))
    if price_cents is None:
        return []
    return [
        {
            "external_variant_id": str(ld_product.get("sku") or ld_product.get("productID") or ld_product.get("url") or "default"),
            "label": "Default",
            "weight_grams": _parse_weight_grams(ld_product.get("name", "")),
            "is_available": "instock" in str(offer.get("availability", "")).lower(),
            "price_cents": price_cents,
            "compare_at_price_cents": None,
            "image_url": "",
        }
    ]


def _crawl_agentic_catalog(
    session: Session,
    merchant: Merchant,
    client: httpx.Client,
    *,
    landing_url: str,
    landing_html: str,
    confidence: float,
) -> CrawlSummary:
    product_links = _extract_product_links(landing_url, landing_html)
    if not product_links:
        return CrawlSummary(
            adapter_name="agentic_catalog",
            records_written=0,
            confidence=confidence * 0.75,
            catalog_strategy=STRATEGY_NONE,
            promo_strategy=STRATEGY_NONE,
            shipping_strategy=STRATEGY_NONE,
            metadata_strategy=STRATEGY_NONE,
        )

    records_written = 0
    _mark_existing_products_inactive(session, merchant)
    for product_url in product_links:
        try:
            response = client.get(product_url)
        except httpx.HTTPError:
            continue
        if response.status_code >= 400 or not response.text:
            continue

        soup = BeautifulSoup(response.text, "lxml")
        ld_product = _extract_ld_product(soup)
        variants = _extract_shopify_variant_payloads(soup)
        page_text = _page_context_text(soup) or _clean_text(response.text)
        description = html.unescape(str(ld_product.get("description") or ""))
        combined_context = "\n".join(part for part in [_clean_text(description), page_text] if part)

        product_name = _normalize_product_name(
            str(ld_product.get("name") or (soup.find("h1").get_text(strip=True) if soup.find("h1") else "") or product_url.rsplit("/", 1)[-1])
        )
        image_candidates = ld_product.get("image") or []
        if isinstance(image_candidates, str):
            image_url = _normalize_asset_url(image_candidates)
        elif isinstance(image_candidates, list):
            image_url = _normalize_asset_url(str(image_candidates[0])) if image_candidates else ""
        else:
            image_url = ""

        external_product_id = str(ld_product.get("productID") or urlparse(product_url).path.rstrip("/"))
        agentic_payload = _apply_metadata_overrides(
            session,
            merchant,
            external_product_id,
            _enrich_payload_with_parser(
                {
                    "name": product_name,
                    "product_url": product_url,
                    "image_url": image_url,
                    "origin_text": _extract_field(combined_context, "Origin") or _infer_origin_from_text(product_name, combined_context),
                    "process_text": _extract_field(combined_context, "Process") or _extract_process_from_text(product_name, combined_context),
                    "variety_text": _extract_field(combined_context, "Variety") or _extract_variety_from_text(product_name, combined_context),
                    "roast_cues": "light" if "light" in combined_context.lower() else "",
                    "tasting_notes_text": _extract_tasting_notes(combined_context),
                    "is_single_origin": _normalize_single_origin_flag(product_name, [], combined_context),
                    "is_espresso_recommended": "espresso" in combined_context.lower(),
                },
                product_name,
                combined_context,
            ),
            product_name,
            combined_context,
        )
        product = _upsert_product(
            session,
            merchant,
            external_product_id,
            agentic_payload,
        )
        session.flush()
        records_written += 1
        _mark_existing_variants_unavailable(product)

        for variant_row in _agentic_variant_rows(ld_product, variants):
            variant = _upsert_variant(
                session,
                product,
                variant_row["external_variant_id"],
                {
                    "label": variant_row["label"],
                    "weight_grams": variant_row["weight_grams"],
                    "is_available": variant_row["is_available"],
                    "is_whole_bean": "ground" not in f"{product_name} {variant_row['label']}".lower(),
                },
            )
            if variant_row["image_url"] and not product.image_url:
                product.image_url = variant_row["image_url"]
            session.flush()
            _record_offer(
                session,
                variant,
                {
                    "price_cents": variant_row["price_cents"],
                    "compare_at_price_cents": variant_row["compare_at_price_cents"],
                    "subscription_price_cents": None,
                    "is_on_sale": bool(
                        variant_row["compare_at_price_cents"] and variant_row["compare_at_price_cents"] > variant_row["price_cents"]
                    ),
                    "is_available": variant_row["is_available"],
                    "source_url": product_url,
                },
            )
            records_written += 1

    return CrawlSummary(
        adapter_name="agentic_catalog",
        records_written=records_written,
        confidence=confidence,
        catalog_strategy=STRATEGY_AGENTIC,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_STRUCTURED,
    )


def _crawl_woocommerce(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    records_written = 0
    promo_buffer: dict[str, PromoCandidate] = {}
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(merchant.homepage_url)
        _record_shipping_policy(session, merchant, merchant.homepage_url, homepage.text, 0.7)
        _record_promos(promo_buffer, merchant.homepage_url, homepage.text, 0.7)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.7, promo_buffer)
        _mark_existing_products_inactive(session, merchant)

        page = 1
        while True:
            resp = client.get(f"{merchant.homepage_url}/wp-json/wc/store/v1/products?per_page=100&page={page}")
            raw_products = resp.json()
            if not raw_products:
                break

            for raw in raw_products:
                categories = [category.get("name", "") for category in raw.get("categories", [])]
                if not _is_coffee_product(raw.get("name", ""), tags=None, categories=categories):
                    continue

                description = _clean_text(raw.get("description", ""))
                price_info = raw.get("prices", {}) or {}
                price_range = price_info.get("price_range") or {}
                min_price = _parse_price_to_cents(price_range.get("min_amount") or price_info.get("price"))
                max_price = _parse_price_to_cents(price_range.get("max_amount") or price_info.get("price"))
                product_url = raw.get("permalink", merchant.homepage_url)
                page_context = _fetch_woocommerce_page_context(client, product_url)
                variation_rows = page_context.variation_rows if raw.get("has_options") else []
                combined_context = "\n".join(part for part in [page_context.summary_text, description] if part)
                intro_tokens = _extract_intro_tokens(combined_context)
                inferred_origin = _infer_origin_from_text(raw.get("name", ""), combined_context)
                first_intro_token = intro_tokens[0] if intro_tokens else ""
                if first_intro_token and "masl" in first_intro_token.lower():
                    first_intro_token = ""

                woo_product_name = _normalize_product_name(raw.get("name", "Unnamed Coffee"))
                woo_payload = _apply_metadata_overrides(
                    session,
                    merchant,
                    str(raw["id"]),
                    _enrich_payload_with_parser(
                        {
                            "name": woo_product_name,
                            "product_url": product_url,
                            "image_url": ((raw.get("images") or [{}])[0].get("src") or ""),
                            "origin_text": _extract_field(description, "Origin") or _merge_origin_and_site(inferred_origin, first_intro_token),
                            "process_text": _extract_field(description, "Process") or _extract_process_from_text(raw.get("name", ""), combined_context),
                            "variety_text": _extract_field(description, "Variety") or _extract_variety_from_text(raw.get("name", ""), combined_context),
                            "roast_cues": "light" if "light" in combined_context.lower() else "",
                            "tasting_notes_text": _extract_tasting_notes(combined_context),
                            "is_single_origin": _normalize_single_origin_flag(raw.get("name", ""), [], combined_context, categories),
                            "is_espresso_recommended": "espresso" in combined_context.lower(),
                        },
                        woo_product_name,
                        combined_context,
                    ),
                    woo_product_name,
                    combined_context,
                )
                product = _upsert_product(
                    session,
                    merchant,
                    str(raw["id"]),
                    woo_payload,
                )
                session.flush()
                records_written += 1
                _mark_existing_variants_unavailable(product)

                size_terms: list[str] = []
                for attribute in raw.get("attributes", []):
                    if attribute.get("name", "").lower() == "size":
                        size_terms = [term.get("name", "") for term in attribute.get("terms", [])]
                        break

                if not size_terms:
                    size_terms = [raw.get("name", "Default")]

                name_map = _variation_name_map(raw.get("attributes", []))
                exact_rows = []
                for row in variation_rows:
                    attributes = row.get("attributes", {}) or {}
                    size_value = None
                    grind_value = None
                    for key, value in attributes.items():
                        lowered_key = key.lower()
                        if "whole-bean-or-ground" in lowered_key or "grind" in lowered_key:
                            grind_value = value
                        elif value:
                            size_value = value
                    if size_value is None:
                        continue
                    if grind_value and "whole-bean" not in grind_value.lower():
                        continue
                    variation_id = row.get("variation_id")
                    weight_hint = str(row.get("weight_html") or row.get("weight") or size_value)
                    exact_rows.append(
                        {
                            "external_variant_id": str(variation_id or f"{raw['id']}::{size_value}"),
                            "label": _normalize_woo_variation_label(str(size_value), name_map),
                            "weight_grams": _parse_weight_grams(weight_hint),
                            "is_available": bool(row.get("is_in_stock", raw.get("is_in_stock", True))),
                            "price_cents": int(round(float(row.get("display_price", 0)) * 100)),
                            "compare_at_price_cents": int(round(float(row.get("display_regular_price", 0)) * 100)) if row.get("display_regular_price") else None,
                        }
                    )

                if exact_rows:
                    variant_rows = exact_rows
                else:
                    variant_prices = _price_range_to_variant_prices(size_terms, min_price, max_price)
                    variant_rows = [
                        {
                            "external_variant_id": f"{raw['id']}::{size_label}",
                            "label": size_label,
                            "weight_grams": _parse_weight_grams(size_label),
                            "is_available": raw.get("is_in_stock", True),
                            "price_cents": variant_prices[idx],
                            "compare_at_price_cents": None,
                        }
                        for idx, size_label in enumerate(size_terms)
                    ]

                for variant_row in variant_rows:
                    _record_shipping_variant_promo(promo_buffer, product.product_url, variant_row["label"], 0.8)
                    variant = _upsert_variant(
                        session,
                        product,
                        variant_row["external_variant_id"],
                        {
                            "label": variant_row["label"],
                            "weight_grams": variant_row["weight_grams"],
                            "is_available": variant_row["is_available"],
                            "is_whole_bean": "ground" not in raw.get("name", "").lower(),
                        },
                    )
                    session.flush()
                    _record_offer(
                        session,
                        variant,
                        {
                            "price_cents": variant_row["price_cents"],
                            "compare_at_price_cents": variant_row["compare_at_price_cents"],
                            "subscription_price_cents": None,
                            "is_on_sale": bool(raw.get("on_sale")) or bool(
                                variant_row["compare_at_price_cents"] and variant_row["compare_at_price_cents"] > variant_row["price_cents"]
                            ),
                            "is_available": variant_row["is_available"],
                            "source_url": product.product_url,
                        },
                    )
                    records_written += 1

            total_pages = int(resp.headers.get("x-wp-totalpages", "1"))
            if page >= total_pages:
                break
            page += 1

    _flush_promos(session, merchant, promo_buffer)
    return CrawlSummary(
        adapter_name="woocommerce",
        records_written=records_written,
        confidence=0.8,
        catalog_strategy=STRATEGY_FEED,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_DOM,
    )


def _crawl_generic(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    promo_buffer: dict[str, PromoCandidate] = {}
    landing_url = _strip_query_fragment(merchant.homepage_url)
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(landing_url)
        _record_shipping_policy(session, merchant, landing_url, homepage.text, 0.4)
        _record_promos(promo_buffer, landing_url, homepage.text, 0.4)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.4, promo_buffer)
        summary = _crawl_agentic_catalog(
            session,
            merchant,
            client,
            landing_url=landing_url,
            landing_html=homepage.text,
            confidence=0.55,
        )
    _flush_promos(session, merchant, promo_buffer)
    if summary.records_written:
        return summary
    return CrawlSummary(
        adapter_name="generic",
        records_written=0,
        confidence=0.4,
        catalog_strategy=STRATEGY_NONE,
        promo_strategy=STRATEGY_DOM,
        shipping_strategy=STRATEGY_DOM,
        metadata_strategy=STRATEGY_NONE,
    )
