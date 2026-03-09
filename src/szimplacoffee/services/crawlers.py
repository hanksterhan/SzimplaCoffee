from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import math
import re
from typing import Iterable

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CrawlRun, Merchant, OfferSnapshot, Product, ProductVariant, PromoSnapshot, ShippingPolicy

USER_AGENT = "SzimplaCoffeeBot/0.1 (+local-first research utility)"


@dataclass
class CrawlSummary:
    adapter_name: str
    records_written: int
    confidence: float


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _clean_text(html: str) -> str:
    text = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _extract_field(text: str, label: str) -> str:
    pattern = re.compile(rf"{re.escape(label)}\s*:?\s*(.+)", re.IGNORECASE)
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
    match = re.search(r"(?:code|promo code)\s+([A-Z0-9]{4,16})", text, re.IGNORECASE)
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
    return ""


def _is_coffee_product(name: str, product_type: str = "", tags: Iterable[str] | None = None, categories: Iterable[str] | None = None) -> bool:
    haystacks = [name, product_type]
    if tags:
        haystacks.extend(tags)
    if categories:
        haystacks.extend(categories)
    text = " ".join(haystacks).lower()
    negative_keywords = [
        "filter",
        "filters",
        "mug",
        "cup",
        "kettle",
        "grinder",
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
    product.origin_text = payload.get("origin_text", "")
    product.process_text = payload.get("process_text", "")
    product.variety_text = payload.get("variety_text", "")
    product.roast_cues = payload.get("roast_cues", "")
    product.tasting_notes_text = payload.get("tasting_notes_text", "")
    product.is_single_origin = payload.get("is_single_origin", False)
    product.is_espresso_recommended = payload.get("is_espresso_recommended", False)
    product.is_active = True
    product.last_seen_at = _utcnow()
    return product


def _mark_existing_products_inactive(session: Session, merchant: Merchant) -> None:
    for product in session.scalars(select(Product).where(Product.merchant_id == merchant.id)).all():
        product.is_active = False


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


def _candidate_policy_urls(homepage_url: str, html: str) -> list[str]:
    candidates = {
        f"{homepage_url}/pages/faq",
        f"{homepage_url}/pages/shipping",
        f"{homepage_url}/pages/subscriptions",
        f"{homepage_url}/policies/shipping-policy",
        f"{homepage_url}/policies/refund-policy",
    }
    soup = BeautifulSoup(html, "lxml")
    for link in soup.select("a[href]"):
        href = (link.get("href") or "").strip()
        text = link.get_text(" ", strip=True).lower()
        if any(term in text for term in ["shipping", "faq", "subscription", "subscribe", "sale", "offer", "office coffee"]):
            if href.startswith("http://") or href.startswith("https://"):
                candidates.add(href.rstrip("/"))
            elif href.startswith("/"):
                candidates.add(f"{homepage_url}{href}".rstrip("/"))
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


def _record_promos(session: Session, merchant: Merchant, homepage_url: str, html: str, confidence: float) -> None:
    text = _clean_text(html)
    threshold = _extract_free_shipping_threshold(text)
    discount_percent = _extract_discount_percent(text)
    discount_dollars = _extract_discount_dollars(text)
    subscription_discount = _extract_subscription_discount(text)
    code = _extract_code(text)
    if threshold:
        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=_utcnow(),
                promo_type="free_shipping",
                title="Free shipping",
                details=f"Free shipping on orders over ${threshold / 100:.0f}",
                source_url=homepage_url,
                estimated_value_cents=800,
                confidence=confidence,
            )
        )
    if discount_percent:
        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=_utcnow(),
                promo_type="percent_off",
                title=f"{discount_percent}% off",
                details=f"{discount_percent}% off detected on homepage",
                code=code,
                source_url=homepage_url,
                estimated_value_cents=discount_percent * 100,
                confidence=confidence * 0.9,
            )
        )
    if discount_dollars:
        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=_utcnow(),
                promo_type="dollar_off",
                title=f"Save ${discount_dollars / 100:.0f}",
                details=f"Saw save amount on homepage",
                code=code,
                source_url=homepage_url,
                estimated_value_cents=discount_dollars,
                confidence=confidence * 0.9,
            )
        )
    if subscription_discount:
        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=_utcnow(),
                promo_type="subscription_discount",
                title=f"{subscription_discount}% subscription savings",
                details="Detected subscription savings language",
                source_url=homepage_url,
                estimated_value_cents=subscription_discount * 100,
                confidence=confidence * 0.9,
            )
        )
    if code and not threshold and not discount_percent and not discount_dollars:
        session.add(
            PromoSnapshot(
                merchant_id=merchant.id,
                observed_at=_utcnow(),
                promo_type="promo_code",
                title=f"Promo code {code}",
                details="Detected promo code on homepage",
                code=code,
                source_url=homepage_url,
                estimated_value_cents=None,
                confidence=confidence * 0.8,
            )
        )


def _crawl_policy_pages(session: Session, merchant: Merchant, client: httpx.Client, homepage_html: str, confidence: float) -> None:
    for policy_url in _candidate_policy_urls(merchant.homepage_url, homepage_html):
        try:
            response = client.get(policy_url)
        except httpx.HTTPError:
            continue
        if response.status_code >= 400 or not response.text:
            continue
        _record_shipping_policy(session, merchant, policy_url, response.text, confidence * 0.9)
        _record_promos(session, merchant, policy_url, response.text, confidence * 0.9)


def _record_shipping_variant_promo(
    session: Session,
    merchant: Merchant,
    source_url: str,
    variant_label: str,
    confidence: float,
) -> None:
    if "ships free" not in variant_label.lower():
        return
    session.add(
        PromoSnapshot(
            merchant_id=merchant.id,
            observed_at=_utcnow(),
            promo_type="free_shipping_variant",
            title="Free shipping variant",
            details=f"{variant_label} includes free shipping",
            source_url=source_url,
            estimated_value_cents=800,
            confidence=confidence * 0.85,
        )
    )


def crawl_merchant(session: Session, merchant: Merchant) -> CrawlSummary:
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name=merchant.platform_type,
        status="started",
        confidence=0.0,
        records_written=0,
    )
    session.add(run)
    session.flush()

    try:
        if merchant.platform_type == "shopify":
            summary = _crawl_shopify(session, merchant)
        elif merchant.platform_type == "woocommerce":
            summary = _crawl_woocommerce(session, merchant)
        else:
            summary = _crawl_generic(session, merchant)

        run.finished_at = _utcnow()
        run.status = "completed"
        run.confidence = summary.confidence
        run.records_written = summary.records_written
        return summary
    except Exception as exc:
        run.finished_at = _utcnow()
        run.status = "failed"
        run.error_summary = str(exc)
        raise


def _crawl_shopify(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    records_written = 0
    _mark_existing_products_inactive(session, merchant)
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(merchant.homepage_url)
        _record_shipping_policy(session, merchant, merchant.homepage_url, homepage.text, 0.9)
        _record_promos(session, merchant, merchant.homepage_url, homepage.text, 0.9)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.9)
        resp = client.get(f"{merchant.homepage_url}/products.json?limit=250")
        payload = resp.json()
        products = payload.get("products", [])

        for raw in products:
            tags = raw.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if not _is_coffee_product(raw.get("title", ""), raw.get("product_type", ""), tags=tags):
                continue

            text = _clean_text(raw.get("body_html", ""))
            product = _upsert_product(
                session,
                merchant,
                str(raw["id"]),
                {
                    "name": raw.get("title", "Unnamed Coffee"),
                    "product_url": f"{merchant.homepage_url}/products/{raw.get('handle', '')}",
                    "origin_text": _extract_field(text, "Origin"),
                    "process_text": _extract_field(text, "Process"),
                    "variety_text": _extract_field(text, "Variety"),
                    "roast_cues": "light" if "light" in " ".join(tags).lower() else "",
                    "tasting_notes_text": _extract_tasting_notes(text),
                    "is_single_origin": _normalize_single_origin_flag(raw.get("title", ""), tags, text),
                    "is_espresso_recommended": "espresso" in " ".join(tags).lower() or "recommended for espresso" in text.lower(),
                },
            )
            session.flush()
            records_written += 1

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

    return CrawlSummary(adapter_name="shopify", records_written=records_written, confidence=0.95)


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


def _crawl_woocommerce(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    records_written = 0
    _mark_existing_products_inactive(session, merchant)
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(merchant.homepage_url)
        _record_shipping_policy(session, merchant, merchant.homepage_url, homepage.text, 0.7)
        _record_promos(session, merchant, merchant.homepage_url, homepage.text, 0.7)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.7)

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

                product = _upsert_product(
                    session,
                    merchant,
                    str(raw["id"]),
                    {
                        "name": raw.get("name", "Unnamed Coffee"),
                        "product_url": raw.get("permalink", merchant.homepage_url),
                        "origin_text": _extract_field(description, "Origin"),
                        "process_text": _extract_field(description, "Process"),
                        "variety_text": _extract_field(description, "Variety"),
                        "roast_cues": "light" if "light" in description.lower() else "",
                        "tasting_notes_text": _extract_tasting_notes(description),
                        "is_single_origin": _normalize_single_origin_flag(raw.get("name", ""), [], description, categories),
                        "is_espresso_recommended": "espresso" in description.lower(),
                    },
                )
                session.flush()
                records_written += 1

                size_terms: list[str] = []
                for attribute in raw.get("attributes", []):
                    if attribute.get("name", "").lower() == "size":
                        size_terms = [term.get("name", "") for term in attribute.get("terms", [])]
                        break

                if not size_terms:
                    size_terms = [raw.get("name", "Default")]

                variant_prices = _price_range_to_variant_prices(size_terms, min_price, max_price)
                for idx, size_label in enumerate(size_terms):
                    _record_shipping_variant_promo(session, merchant, product.product_url, size_label, 0.8)
                    variant = _upsert_variant(
                        session,
                        product,
                        f"{raw['id']}::{size_label}",
                        {
                            "label": size_label,
                            "weight_grams": _parse_weight_grams(size_label),
                            "is_available": raw.get("is_in_stock", True),
                            "is_whole_bean": "ground" not in raw.get("name", "").lower(),
                        },
                    )
                    session.flush()
                    _record_offer(
                        session,
                        variant,
                        {
                            "price_cents": variant_prices[idx],
                            "compare_at_price_cents": None,
                            "subscription_price_cents": None,
                            "is_on_sale": bool(raw.get("on_sale")),
                            "is_available": raw.get("is_in_stock", True),
                            "source_url": product.product_url,
                        },
                    )
                    records_written += 1

            total_pages = int(resp.headers.get("x-wp-totalpages", "1"))
            if page >= total_pages:
                break
            page += 1

    return CrawlSummary(adapter_name="woocommerce", records_written=records_written, confidence=0.8)


def _crawl_generic(session: Session, merchant: Merchant) -> CrawlSummary:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        homepage = client.get(merchant.homepage_url)
        _record_shipping_policy(session, merchant, merchant.homepage_url, homepage.text, 0.4)
        _record_promos(session, merchant, merchant.homepage_url, homepage.text, 0.4)
        _crawl_policy_pages(session, merchant, client, homepage.text, 0.4)
    return CrawlSummary(adapter_name="generic", records_written=0, confidence=0.4)
