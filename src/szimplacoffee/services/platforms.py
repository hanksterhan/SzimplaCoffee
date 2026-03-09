from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


USER_AGENT = "SzimplaCoffeeBot/0.1 (+local-first research utility)"


@dataclass
class PlatformDetection:
    normalized_url: str
    domain: str
    merchant_name: str
    platform_type: str
    confidence: float


def normalize_url(raw_url: str) -> str:
    candidate = raw_url.strip()
    if not candidate.startswith(("http://", "https://")):
        candidate = f"https://{candidate}"
    return candidate.rstrip("/")


def extract_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def guess_name_from_domain(domain: str) -> str:
    stem = domain.split(".")[0].replace("-", " ").replace("_", " ")
    return stem.title()


def _extract_name_from_html(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    for selector in [
        ('meta[property="og:site_name"]', "content"),
        ('meta[name="application-name"]', "content"),
    ]:
        node = soup.select_one(selector[0])
        if node and node.get(selector[1]):
            return node.get(selector[1]).strip()
    if soup.title and soup.title.text:
        title = soup.title.text.strip()
        if "|" in title:
            return title.split("|", 1)[0].strip()
        if " - " in title:
            return title.split(" - ", 1)[0].strip()
        return title
    return None


def _has_internal_shop_links(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    for link in soup.select("a[href]"):
        href = (link.get("href") or "").lower()
        text = link.get_text(" ", strip=True).lower()
        if href.startswith("/") and any(term in href for term in ["/shop", "/product", "/coffee", "/collections"]):
            return True
        if any(term in text for term in ["shop", "coffee", "subscribe"]) and href.startswith("/"):
            return True
    return False


def _is_squarespace_commerce(html: str) -> bool:
    body = html.lower()
    return "this is squarespace" in body and _has_internal_shop_links(html) and "coffee" in body


def _is_custom_commerce(html: str) -> bool:
    body = html.lower()
    signals = 0
    if _has_internal_shop_links(html):
        signals += 1
    if any(term in body for term in ["cart", "add to cart", "shop fresh roasted", "whole bean", "single origin"]):
        signals += 1
    if any(term in body for term in ["application/ld+json", "\"product\"", "\"offers\""]):
        signals += 1
    return signals >= 2 and "coffee" in body


def detect_platform(raw_url: str, timeout: float = 10.0) -> PlatformDetection:
    normalized_url = normalize_url(raw_url)
    domain = extract_domain(normalized_url)
    merchant_name = guess_name_from_domain(domain)
    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        homepage_html: str | None = None
        wc_url = f"{normalized_url}/wp-json/wc/store/v1/products?per_page=1"
        try:
            wc_resp = client.get(wc_url)
            if wc_resp.status_code == 200 and wc_resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    home = client.get(normalized_url)
                    homepage_html = home.text
                except httpx.HTTPError:
                    homepage_html = None
                resolved_name = _extract_name_from_html(homepage_html or "") or merchant_name
                return PlatformDetection(normalized_url, domain, resolved_name, "woocommerce", 0.95)
        except httpx.HTTPError:
            pass

        shopify_url = f"{normalized_url}/products.json?limit=1"
        try:
            shopify_resp = client.get(shopify_url)
            if shopify_resp.status_code == 200:
                payload = shopify_resp.json()
                if isinstance(payload, dict) and "products" in payload:
                    try:
                        home = client.get(normalized_url)
                        homepage_html = home.text
                    except httpx.HTTPError:
                        homepage_html = None
                    resolved_name = _extract_name_from_html(homepage_html or "") or merchant_name
                    return PlatformDetection(normalized_url, domain, resolved_name, "shopify", 0.95)
        except (ValueError, httpx.HTTPError):
            pass

        try:
            home = client.get(normalized_url)
            body = home.text.lower()
            merchant_name = _extract_name_from_html(home.text) or merchant_name
            if "cdn.shopify.com" in body or "myshopify.com" in body:
                return PlatformDetection(normalized_url, domain, merchant_name, "shopify", 0.7)
            if "woocommerce" in body or "wp-content/plugins/woocommerce" in body:
                return PlatformDetection(normalized_url, domain, merchant_name, "woocommerce", 0.7)
            if _is_squarespace_commerce(home.text):
                return PlatformDetection(normalized_url, domain, merchant_name, "squarespace", 0.82)
            if _is_custom_commerce(home.text):
                return PlatformDetection(normalized_url, domain, merchant_name, "custom", 0.72)
        except httpx.HTTPError:
            pass

    return PlatformDetection(normalized_url, domain, merchant_name, "unknown", 0.3)
