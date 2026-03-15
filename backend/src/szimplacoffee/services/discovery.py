from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Merchant, MerchantCandidate, MerchantQualityProfile, MerchantSource
from .platforms import PlatformDetection, detect_platform, extract_domain, recommended_crawl_tier


# ---------------------------------------------------------------------------
# SC-53: Merchant registry tiers and inclusion thresholds
# ---------------------------------------------------------------------------

# Trust tiers for merchant registry
TRUST_TIER_TRUSTED = "trusted"
TRUST_TIER_VERIFIED = "verified"
TRUST_TIER_CANDIDATE = "candidate"
TRUST_TIER_REJECTED = "rejected"

# Crawl tiers for crawl frequency
CRAWL_TIER_A = "A"  # High-value: crawled every 6h
CRAWL_TIER_B = "B"  # Promising: crawled every 24h
CRAWL_TIER_C = "C"  # Long-tail: crawled every 7d
CRAWL_TIER_D = "D"  # Excluded: not auto-crawled

# Minimum trust tiers included in buying views (recommendations / Today)
BUYING_VIEW_TRUSTED_TIERS = {TRUST_TIER_TRUSTED, TRUST_TIER_VERIFIED}

# Trust tiers allowed in discovery and catalog browsing (not restricted)
CATALOG_VIEW_TIERS = {TRUST_TIER_TRUSTED, TRUST_TIER_VERIFIED, TRUST_TIER_CANDIDATE}

# Minimum quality score a merchant needs for inclusion in buying recommendations
BUYING_QUALITY_FLOOR = 0.4  # overall_quality_score

# Crawl quality floor for "reliable data" badge
CRAWL_QUALITY_RELIABLE_FLOOR = 0.7


def meets_buying_threshold(merchant: Merchant) -> bool:
    """Return True if a merchant is eligible to appear in buying recommendations."""
    if not merchant.is_active:
        return False
    if merchant.trust_tier not in CATALOG_VIEW_TIERS:
        return False
    if merchant.crawl_tier == CRAWL_TIER_D:
        return False
    if merchant.quality_profile:
        return merchant.quality_profile.overall_quality_score >= BUYING_QUALITY_FLOOR
    return True  # no profile yet → assume eligible (optimistic for new merchants)


DISCOVERY_QUERIES = [
    "specialty coffee roaster united states",
    "single origin coffee roaster usa",
    "best coffee roasters in america",
]
DISCOVERY_BLOCKLIST = {
    "amazon.com",
    "bsky.app",
    "facebook.com",
    "flipboard.com",
    "instagram.com",
    "linkedin.com",
    "maps.apple.com",
    "medium.com",
    "pinterest.com",
    "reddit.com",
    "sprudge.com",
    "stackexchange.com",
    "stackoverflow.com",
    "static.com",
    "thrillist.com",
    "tripadvisor.com",
    "twitter.com",
    "x.com",
    "yelp.com",
    "youtube.com",
}
LISTICLE_HINTS = {
    "best",
    "top",
    "guide",
    "ranked",
    "roasters",
    "brands",
    "america",
    "united states",
}
COFFEE_POSITIVE_TERMS = {
    "coffee",
    "roaster",
    "roasting",
    "espresso",
    "whole bean",
    "single origin",
    "subscription",
}
COFFEE_NEGATIVE_TERMS = {
    "awards",
    "charity",
    "championship",
    "championships",
    "competition",
    "directory",
    "donate",
    "foundation",
    "newsletter",
    "non-profit",
    "nonprofit",
    "research",
}
RESULTS_PER_QUERY = 3
USER_AGENT = "Mozilla/5.0 (compatible; SzimplaCoffee/0.1; +local-first research utility)"


@dataclass
class DiscoveryResult:
    created_count: int
    skipped_count: int


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _decode_bing_result_url(href: str) -> str | None:
    if not href:
        return None
    if href.startswith("http://") or href.startswith("https://"):
        parsed = urlparse(href)
        if parsed.netloc.lower().endswith("bing.com") and parsed.path.startswith("/ck/a"):
            encoded = parse_qs(parsed.query).get("u", [None])[0]
            if not encoded:
                return href
            if encoded.startswith("a1"):
                encoded = encoded[2:]
            padded = encoded + ("=" * (-len(encoded) % 4))
            try:
                return base64.urlsafe_b64decode(padded).decode("utf-8")
            except Exception:
                return href
        return href
    return None


def _is_blocked_domain(domain: str) -> bool:
    return any(blocked in domain for blocked in DISCOVERY_BLOCKLIST)


def _is_probable_listicle(url: str, title: str) -> bool:
    haystack = f"{url} {title}".lower()
    return any(hint in haystack for hint in LISTICLE_HINTS)


def _search_result_urls(query: str, limit: int = RESULTS_PER_QUERY) -> list[tuple[str, str]]:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        response = client.get("https://www.bing.com/search", params={"q": query})
        soup = BeautifulSoup(response.text, "lxml")
        urls: list[tuple[str, str]] = []
        for link in soup.select("li.b_algo h2 a"):
            resolved = _decode_bing_result_url(link.get("href", ""))
            if not resolved:
                continue
            domain = extract_domain(resolved)
            if _is_blocked_domain(domain):
                continue
            title = link.get_text(" ", strip=True)
            urls.append((resolved, title))
            if len(urls) >= limit:
                break
    return urls


def _normalize_candidate_url(href: str, source_url: str) -> str | None:
    if not href:
        return None
    absolute = urljoin(source_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    domain = extract_domain(absolute)
    if not domain or _is_blocked_domain(domain):
        return None
    if parsed.path.lower().endswith((".jpg", ".jpeg", ".png", ".svg", ".pdf", ".webp")):
        return None
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _root_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _harvest_domains_from_source(source_url: str, max_domains: int = 6) -> list[str]:
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        response = client.get(source_url)
        soup = BeautifulSoup(response.text, "lxml")
    source_domain = extract_domain(source_url)
    domains: list[str] = []
    seen: set[str] = set()
    for link in soup.select("a[href]"):
        normalized = _normalize_candidate_url(link.get("href", ""), source_url)
        if not normalized:
            continue
        domain = extract_domain(normalized)
        if domain == source_domain or domain in seen:
            continue
        text = link.get_text(" ", strip=True).lower()
        if not text and domain.count(".") > 1:
            continue
        seen.add(domain)
        domains.append(_root_url(normalized))
        if len(domains) >= max_domains:
            break
    return domains


def _candidate_record_exists(session: Session, domain: str) -> bool:
    return bool(session.scalar(select(Merchant.id).where(Merchant.canonical_domain == domain))) or bool(
        session.scalar(select(MerchantCandidate.id).where(MerchantCandidate.canonical_domain == domain))
    )


def _promotable_detection(detection: PlatformDetection) -> bool:
    if detection.platform_type in {"shopify", "woocommerce"}:
        return True
    if detection.platform_type in {"squarespace", "custom"}:
        return detection.confidence >= 0.72
    return detection.confidence >= 0.7 and "coffee" in detection.merchant_name.lower()


def _looks_like_coffee_merchant(homepage_url: str, detection: PlatformDetection) -> bool:
    name_haystack = f"{detection.domain} {detection.merchant_name}".lower()
    if any(term in name_haystack for term in COFFEE_NEGATIVE_TERMS):
        return False
    headers = {"User-Agent": USER_AGENT}
    try:
        response = httpx.get(homepage_url, headers=headers, follow_redirects=True, timeout=3.0)
    except httpx.HTTPError:
        return False
    text = BeautifulSoup(response.text, "lxml").get_text(" ", strip=True).lower()[:5000]
    if any(term in text for term in COFFEE_NEGATIVE_TERMS):
        return False
    positive_hits = sum(term in text or term in name_haystack for term in COFFEE_POSITIVE_TERMS)
    if any(term in name_haystack for term in ["coffee", "roast", "espresso", "cafe"]):
        return positive_hits >= 1
    return positive_hits >= 2


def _obvious_coffee_brand(detection: PlatformDetection) -> bool:
    haystack = f"{detection.domain} {detection.merchant_name}".lower()
    return any(term in haystack for term in ["coffee", "roast", "espresso", "cafe"])


def _strong_platform_coffee_merchant(detection: PlatformDetection) -> bool:
    if detection.platform_type in {"shopify", "woocommerce"}:
        return detection.confidence >= 0.95
    if detection.platform_type == "squarespace":
        return detection.confidence >= 0.8
    if detection.platform_type == "custom":
        return detection.confidence >= 0.72
    return False


def _safe_obvious_brand(detection: PlatformDetection) -> bool:
    haystack = f"{detection.domain} {detection.merchant_name}".lower()
    if any(term in haystack for term in COFFEE_NEGATIVE_TERMS):
        return False
    if any(term in haystack for term in ["roast", "roaster", "espresso", "cafe"]):
        return True
    return "coffee" in haystack and _strong_platform_coffee_merchant(detection)


def _create_candidate(
    session: Session,
    detection: PlatformDetection,
    query: str,
    note: str,
) -> bool:
    if _candidate_record_exists(session, detection.domain):
        return False
    session.add(
        MerchantCandidate(
            canonical_domain=detection.domain,
            merchant_name=detection.merchant_name,
            homepage_url=detection.normalized_url,
            source_query=query,
            platform_type=detection.platform_type,
            confidence=detection.confidence,
            status="pending",
            notes=note,
            discovered_at=_utcnow(),
        )
    )
    return True


def run_discovery(session: Session, queries: Iterable[str] | None = None) -> DiscoveryResult:
    created = 0
    skipped = 0
    for query in queries or DISCOVERY_QUERIES:
        for result_url, title in _search_result_urls(query):
            is_listicle = _is_probable_listicle(result_url, title)
            detection = detect_platform(_root_url(result_url), timeout=3.0)
            direct_candidate_ok = False
            if not is_listicle and _promotable_detection(detection):
                direct_candidate_ok = _safe_obvious_brand(detection) or _looks_like_coffee_merchant(detection.normalized_url, detection)
            if direct_candidate_ok:
                if _create_candidate(session, detection, query, f"Discovered from search result: {title}"):
                    created += 1
                else:
                    skipped += 1
                continue

            if not is_listicle:
                skipped += 1
                continue

            try:
                harvested_urls = _harvest_domains_from_source(result_url)
            except httpx.HTTPError:
                skipped += 1
                continue

            for candidate_url in harvested_urls:
                harvested_detection = detect_platform(_root_url(candidate_url), timeout=3.0)
                if not _strong_platform_coffee_merchant(harvested_detection) and not _obvious_coffee_brand(harvested_detection):
                    skipped += 1
                    continue
                if not _safe_obvious_brand(harvested_detection) and not _looks_like_coffee_merchant(
                    harvested_detection.normalized_url,
                    harvested_detection,
                ):
                    skipped += 1
                    continue
                if _create_candidate(
                    session,
                    harvested_detection,
                    query,
                    f"Harvested from {result_url}",
                ):
                    created += 1
                else:
                    skipped += 1
    return DiscoveryResult(created_count=created, skipped_count=skipped)


def promote_candidate(session: Session, candidate: MerchantCandidate, crawl_tier: str | None = None) -> Merchant:
    merchant = Merchant(
        name=candidate.merchant_name,
        canonical_domain=candidate.canonical_domain,
        homepage_url=candidate.homepage_url,
        platform_type=candidate.platform_type,
        crawl_tier=crawl_tier or recommended_crawl_tier(candidate.platform_type, candidate.confidence),
        trust_tier="candidate",
    )
    session.add(merchant)
    session.flush()
    session.add(
        MerchantSource(
            merchant_id=merchant.id,
            source_type="discovery",
            source_value=candidate.homepage_url,
            confidence=candidate.confidence,
        )
    )
    session.add(
        MerchantQualityProfile(
            merchant_id=merchant.id,
            freshness_transparency_score=0.55,
            shipping_clarity_score=0.5,
            metadata_quality_score=0.6 if candidate.platform_type in {"shopify", "woocommerce"} else 0.5,
            espresso_relevance_score=0.55,
            service_confidence_score=0.5,
            overall_quality_score=0.55,
        )
    )
    candidate.status = "promoted"
    candidate.reviewed_at = _utcnow()
    return merchant
