from __future__ import annotations

import argparse

from .bootstrap import bootstrap_if_empty, init_db
from .db import session_scope
from .models import Merchant
from .services.crawlers import crawl_merchant
from .services.platforms import detect_platform
from .services.recommendations import RecommendationRequest, build_recommendations


def main() -> None:
    parser = argparse.ArgumentParser(prog="szimpla")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap")

    add_parser = subparsers.add_parser("add-merchant")
    add_parser.add_argument("url")
    add_parser.add_argument("--crawl-now", action="store_true")

    subparsers.add_parser("crawl-all")
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
            merchant = Merchant(
                name=detection.merchant_name,
                canonical_domain=detection.domain,
                homepage_url=detection.normalized_url,
                platform_type=detection.platform_type,
            )
            session.add(merchant)
            session.flush()
            if args.crawl_now:
                crawl_merchant(session, merchant)
            print(f"Added merchant {merchant.name} ({merchant.platform_type})")
            return

        if args.command == "crawl-all":
            for merchant in session.query(Merchant).all():
                crawl_merchant(session, merchant)
                print(f"Crawled {merchant.name}")
            return

        if args.command == "recommend":
            candidates = build_recommendations(
                session,
                RecommendationRequest(
                    shot_style="modern_58mm",
                    quantity_mode="12-18 oz",
                    bulk_allowed=False,
                ),
            )
            for candidate in candidates:
                print(f"{candidate.score:.3f} {candidate.merchant_name} | {candidate.product_name} | {candidate.variant_label}")


if __name__ == "__main__":
    main()

