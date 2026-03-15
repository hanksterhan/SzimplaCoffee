from __future__ import annotations

import argparse

from sqlalchemy import select

from .bootstrap import bootstrap_if_empty, init_db
from .db import session_scope
from .models import Merchant
from .services.crawlers import crawl_merchant
from .services.discovery import run_discovery
from .services.platforms import detect_platform, recommended_crawl_tier
from .services.recommendations import RecommendationRequest, build_recommendations


def main() -> None:
    parser = argparse.ArgumentParser(prog="szimpla")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap")

    add_parser = subparsers.add_parser("add-merchant")
    add_parser.add_argument("url")
    add_parser.add_argument("--crawl-now", action="store_true")

    subparsers.add_parser("crawl-all")
    subparsers.add_parser("discover")
    subparsers.add_parser("recommend")

    args = parser.parse_args()
    init_db()

    with session_scope() as session:
        if args.command == "bootstrap":
            bootstrap_if_empty(session)
            print("Bootstrap complete.")
            return

        if args.command == "add-merchant":
            detection = detect_platform(args.url)
            merchant = session.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
            if merchant is None:
                merchant = Merchant(
                    name=detection.merchant_name,
                    canonical_domain=detection.domain,
                    homepage_url=detection.normalized_url,
                    platform_type=detection.platform_type,
                    crawl_tier=recommended_crawl_tier(detection.platform_type, detection.confidence),
                )
                session.add(merchant)
                session.flush()
                action = "Added"
            else:
                merchant.name = detection.merchant_name
                merchant.homepage_url = detection.normalized_url
                merchant.platform_type = detection.platform_type
                merchant.crawl_tier = recommended_crawl_tier(detection.platform_type, detection.confidence)
                action = "Updated"
            if args.crawl_now:
                crawl_merchant(session, merchant)
            print(f"{action} merchant {merchant.name} ({merchant.platform_type})")
            return

        if args.command == "crawl-all":
            for merchant in session.query(Merchant).all():
                try:
                    crawl_merchant(session, merchant)
                    print(f"Crawled {merchant.name}")
                except Exception as exc:
                    print(f"Failed {merchant.name}: {exc}")
            return

        if args.command == "discover":
            result = run_discovery(session)
            print(f"Discovery complete. Created={result.created_count} skipped={result.skipped_count}")
            return

        if args.command == "recommend":
            candidates = build_recommendations(
                session,
                RecommendationRequest(
                    shot_style="modern_58mm",
                    quantity_mode="12-18 oz",
                    bulk_allowed=False,
                    allow_decaf=False,
                ),
            )
            for candidate in candidates:
                print(f"{candidate.score:.3f} {candidate.merchant_name} | {candidate.product_name} | {candidate.variant_label}")


if __name__ == "__main__":
    main()
