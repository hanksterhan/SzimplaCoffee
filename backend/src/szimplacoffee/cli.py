from __future__ import annotations

import argparse

from sqlalchemy import select

from .bootstrap import bootstrap_if_empty, init_db
from .db import session_scope
from .models import Merchant, Product
from .services.crawlers import crawl_merchant
from .services.discovery import run_discovery
from .services.platforms import detect_platform, recommended_crawl_tier
from .services.quality_scorer import score_all_merchants
from .services.recommendations import RecommendationRequest, build_recommendations
from .services.scheduler import get_crawl_schedule, get_merchants_due_for_crawl


def main() -> None:
    parser = argparse.ArgumentParser(prog="szimpla")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap")

    add_parser = subparsers.add_parser("add-merchant")
    add_parser.add_argument("url")
    add_parser.add_argument("--crawl-now", action="store_true")

    # SC-59: bulk merchant import from file
    import_parser = subparsers.add_parser(
        "import-merchants",
        help="Import merchants from a newline-delimited URL file (# comments and blank lines ignored).",
    )
    import_parser.add_argument("--file", required=True, metavar="FILE", help="Path to URL list file")

    subparsers.add_parser("crawl-all")
    subparsers.add_parser("discover")
    subparsers.add_parser("recommend")

    # SC-31: backfill-metadata
    subparsers.add_parser(
        "backfill-metadata",
        help="Re-run coffee metadata parser over all products and fill empty fields.",
    )

    # SC-32: score-merchants
    subparsers.add_parser(
        "score-merchants",
        help="Generate or update quality profiles for all active merchants.",
    )

    # SC-60: promote-tiers
    subparsers.add_parser(
        "promote-tiers",
        help="Review merchant quality profiles and promote/demote crawl and trust tiers accordingly.",
    )

    # SC-33: crawl-schedule + run-scheduled-crawls
    subparsers.add_parser(
        "crawl-schedule",
        help="Show the crawl schedule and next expected crawl time for each merchant.",
    )
    subparsers.add_parser(
        "run-scheduled-crawls",
        help="Crawl all merchants whose tier interval has elapsed since last crawl.",
    )

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

        if args.command == "import-merchants":
            # SC-59: bulk import from a newline-delimited URL file
            import re

            _URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

            filepath = args.file
            try:
                with open(filepath, encoding="utf-8") as fh:
                    raw_lines = fh.readlines()
            except OSError as exc:
                print(f"Error reading file: {exc}")
                return

            urls = [line.strip() for line in raw_lines]
            urls = [u for u in urls if u and not u.startswith("#")]

            imported = 0
            skipped = 0
            failed = 0

            for url in urls:
                # Fast-reject obviously invalid entries before any network call
                candidate = url if url.startswith("http://") or url.startswith("https://") else f"https://{url}"
                if not _URL_RE.match(candidate) or "." not in candidate.split("//", 1)[-1]:
                    print(f"  Failed (invalid URL): {url}")
                    failed += 1
                    continue
                try:
                    detection = detect_platform(url)
                    existing = session.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
                    if existing is not None:
                        print(f"  Skipped (already exists): {url}")
                        skipped += 1
                        continue
                    merchant = Merchant(
                        name=detection.merchant_name,
                        canonical_domain=detection.domain,
                        homepage_url=detection.normalized_url,
                        platform_type=detection.platform_type,
                        crawl_tier=recommended_crawl_tier(detection.platform_type, detection.confidence),
                    )
                    session.add(merchant)
                    session.flush()
                    print(f"  Imported: {merchant.name} ({detection.domain})")
                    imported += 1
                except Exception as exc:
                    print(f"  Failed: {url} — {exc}")
                    failed += 1

            print(f"\nSummary: Imported={imported}, Skipped={skipped}, Failed={failed}")
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
            candidates, _ = build_recommendations(
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
            return

        if args.command == "backfill-metadata":
            # SC-31: re-run coffee metadata parser over all products
            from .services.coffee_parser import parse_coffee_metadata

            products = session.scalars(select(Product)).all()
            updated = 0
            field_counts: dict[str, int] = {
                "origin_text": 0,
                "process_text": 0,
                "variety_text": 0,
                "tasting_notes_text": 0,
                "origin_country": 0,
                "origin_region": 0,
                "process_family": 0,
                "roast_level": 0,
            }
            for product in products:
                parsed = parse_coffee_metadata(product.name, getattr(product, "description_html", "") or "")
                changed = False
                if not product.origin_text and parsed.origin_text:
                    product.origin_text = parsed.origin_text
                    field_counts["origin_text"] += 1
                    changed = True
                if not product.process_text and parsed.process_text:
                    product.process_text = parsed.process_text
                    field_counts["process_text"] += 1
                    changed = True
                if not product.variety_text and parsed.variety_text:
                    product.variety_text = parsed.variety_text
                    field_counts["variety_text"] += 1
                    changed = True
                if not product.tasting_notes_text and parsed.tasting_notes_text:
                    product.tasting_notes_text = parsed.tasting_notes_text
                    field_counts["tasting_notes_text"] += 1
                    changed = True
                if not product.origin_country and parsed.origin_country:
                    product.origin_country = parsed.origin_country
                    field_counts["origin_country"] += 1
                    changed = True
                if not product.origin_region and parsed.origin_region:
                    product.origin_region = parsed.origin_region
                    field_counts["origin_region"] += 1
                    changed = True
                if product.process_family in (None, "", "unknown") and parsed.process_family != "unknown":
                    product.process_family = parsed.process_family
                    field_counts["process_family"] += 1
                    changed = True
                if product.roast_level in (None, "", "unknown") and parsed.roast_level != "unknown":
                    product.roast_level = parsed.roast_level
                    field_counts["roast_level"] += 1
                    changed = True
                if changed:
                    updated += 1

            session.flush()
            total = len(products)
            print(f"Backfill complete. Updated {updated}/{total} products.")
            for field, count in field_counts.items():
                if count:
                    pct = count * 100 // total if total else 0
                    print(f"  {field}: {count} ({pct}%)")
            return

        if args.command == "score-merchants":
            # SC-32: generate/update quality profiles for all active merchants
            results = score_all_merchants(session)
            print(f"Scored {len(results)} merchants.")
            for r in sorted(results, key=lambda x: x["overall"], reverse=True):
                print(
                    f"  {r['name']:<40} overall={r['overall']:.2f}"
                    f"  fresh={r['freshness']:.2f}"
                    f"  shipping={r['shipping']:.2f}"
                    f"  metadata={r['metadata']:.2f}"
                    f"  espresso={r['espresso']:.2f}"
                )
            return

        if args.command == "promote-tiers":
            # SC-60: auto-promote/demote merchant tiers based on quality profiles
            # Criteria:
            #   crawl_tier=A: overall_score >= 0.7 AND product_count >= 20
            #   crawl_tier=B: overall_score >= 0.4 AND product_count >= 5 (if not A-eligible)
            #   crawl_tier=D: product_count == 0 AND crawl_run_count >= 1 (crawled but empty)
            #   trust_tier=trusted: promoted when product_count meets tier threshold and was candidate
            from sqlalchemy import func
            from .models import CrawlRun, MerchantQualityProfile  # noqa: F401

            TIER_A_MIN_SCORE = 0.7
            TIER_A_MIN_PRODUCTS = 20
            TIER_B_MIN_SCORE = 0.4
            TIER_B_MIN_PRODUCTS = 5
            # Demote to D after at least 1 completed crawl with zero results
            ZERO_PRODUCT_MIN_CRAWLS = 1

            merchants = session.scalars(select(Merchant).where(Merchant.is_active == True)).all()  # noqa: E712
            promoted_a: list[tuple] = []
            promoted_b: list[tuple] = []
            demoted_d: list[tuple] = []
            trust_promoted: list[tuple] = []
            unchanged: list[tuple] = []

            for merchant in merchants:
                profile = merchant.quality_profile
                overall_score = profile.overall_quality_score if profile else 0.0
                product_count = len(merchant.products)
                crawl_run_count = session.scalar(
                    select(func.count(CrawlRun.id)).where(CrawlRun.merchant_id == merchant.id)
                ) or 0

                old_crawl_tier = merchant.crawl_tier
                crawl_changed = False
                trust_changed = False

                # Demote to D: zero products after at least one completed crawl
                if product_count == 0 and crawl_run_count >= ZERO_PRODUCT_MIN_CRAWLS:
                    if merchant.crawl_tier != "D":
                        merchant.crawl_tier = "D"
                        crawl_changed = True
                        demoted_d.append((merchant.name, old_crawl_tier, overall_score, product_count, crawl_run_count))
                    else:
                        unchanged.append((merchant.name, merchant.crawl_tier, overall_score, product_count, "already D"))
                    continue

                # Promote to A: high score + rich catalog
                if overall_score >= TIER_A_MIN_SCORE and product_count >= TIER_A_MIN_PRODUCTS:
                    if merchant.crawl_tier != "A":
                        merchant.crawl_tier = "A"
                        crawl_changed = True
                        promoted_a.append((merchant.name, old_crawl_tier, overall_score, product_count))
                    if merchant.trust_tier == "candidate":
                        merchant.trust_tier = "trusted"
                        trust_changed = True
                        trust_promoted.append((merchant.name, overall_score, product_count))
                    if not crawl_changed and not trust_changed:
                        unchanged.append((merchant.name, merchant.crawl_tier, overall_score, product_count, "already A/trusted"))
                    continue

                # Promote to B: moderate score + decent catalog (if not A-eligible)
                if overall_score >= TIER_B_MIN_SCORE and product_count >= TIER_B_MIN_PRODUCTS:
                    if merchant.crawl_tier not in ("A", "B"):
                        merchant.crawl_tier = "B"
                        crawl_changed = True
                        promoted_b.append((merchant.name, old_crawl_tier, overall_score, product_count))
                    if merchant.trust_tier == "candidate":
                        merchant.trust_tier = "trusted"
                        trust_changed = True
                        trust_promoted.append((merchant.name, overall_score, product_count))
                    if not crawl_changed and not trust_changed:
                        unchanged.append((merchant.name, merchant.crawl_tier, overall_score, product_count, "already A/B/trusted"))
                    continue

                    # Already at correct tier — check if trust_tier needs upgrade
                if merchant.crawl_tier in ("A", "B") and merchant.trust_tier == "candidate" and product_count >= TIER_B_MIN_PRODUCTS:
                    merchant.trust_tier = "trusted"
                    trust_changed = True
                    trust_promoted.append((merchant.name, overall_score, product_count))
                    continue

                unchanged.append((merchant.name, merchant.crawl_tier, overall_score, product_count, "below threshold"))

            session.flush()

            print("=== Tier Promotion Results ===")
            if promoted_a:
                print(f"\nPromoted to crawl_tier=A ({len(promoted_a)}):")
                for name, old, score, products in promoted_a:
                    print(f"  {name:<40} {old} → A  score={score:.2f}  products={products}")
            if promoted_b:
                print(f"\nPromoted to crawl_tier=B ({len(promoted_b)}):")
                for name, old, score, products in promoted_b:
                    print(f"  {name:<40} {old} → B  score={score:.2f}  products={products}")
            if demoted_d:
                print(f"\nDemoted to crawl_tier=D ({len(demoted_d)}):")
                for name, old, score, products, runs in demoted_d:
                    print(f"  {name:<40} {old} → D  score={score:.2f}  products={products}  crawl_runs={runs}")
            if trust_promoted:
                print(f"\nTrust promoted to trusted ({len(trust_promoted)}):")
                for name, score, products in trust_promoted:
                    print(f"  {name:<40} candidate → trusted  score={score:.2f}  products={products}")
            if unchanged:
                print(f"\nUnchanged ({len(unchanged)}):")
                for entry in unchanged:
                    name, tier, score, products, reason = entry
                    print(f"  {name:<40} tier={tier}  score={score:.2f}  products={products}  ({reason})")

            total_ab = session.scalar(
                select(func.count(Merchant.id)).where(Merchant.crawl_tier.in_(["A", "B"]))
            ) or 0
            total_d = session.scalar(
                select(func.count(Merchant.id)).where(Merchant.crawl_tier == "D")
            ) or 0
            print("\n=== Final Tier Distribution ===")
            for tier in ["A", "B", "C", "D"]:
                count = session.scalar(
                    select(func.count(Merchant.id)).where(Merchant.crawl_tier == tier)
                ) or 0
                print(f"  Tier {tier}: {count} merchant(s)")
            print(f"\nMerchants in A or B: {total_ab}  |  Excluded (D): {total_d}")
            return

        if args.command == "crawl-schedule":
            # SC-33: show crawl schedule for all merchants
            schedule = get_crawl_schedule(session)
            due_ids = {m.id for m in get_merchants_due_for_crawl(session)}
            print(f"{'Merchant':<40} {'Tier':<6} {'Interval':>10} {'Last Crawl':<22} {'Next Due':<22} {'Status'}")
            print("-" * 120)
            for item in sorted(schedule, key=lambda x: (x["next_due_at"] or "", x["name"])):
                is_due = item["merchant_id"] in due_ids
                status = "DUE" if is_due else "ok"
                last = (item["last_crawl_at"] or "never")[:19]
                next_due = (item["next_due_at"] or "unknown")[:19]
                interval = f"{item['interval_hours']}h" if item["interval_hours"] else "n/a"
                print(f"  {item['name']:<40} {item['crawl_tier']:<6} {interval:>10} {last:<22} {next_due:<22} {status}")
            due_count = sum(1 for item in schedule if item["merchant_id"] in due_ids)
            print(f"\n{due_count} merchant(s) currently due for crawl.")
            return

        if args.command == "run-scheduled-crawls":
            # SC-33: crawl all merchants whose tier interval has elapsed
            due_merchants = get_merchants_due_for_crawl(session)
            if not due_merchants:
                print("No merchants are currently due for crawl.")
                return
            print(f"{len(due_merchants)} merchant(s) due for crawl.")
            for merchant in due_merchants:
                try:
                    summary = crawl_merchant(session, merchant)
                    print(f"  Crawled {merchant.name}: {summary.records_written} records ({summary.adapter_name})")
                except Exception as exc:
                    print(f"  Failed {merchant.name}: {exc}")
            return


if __name__ == "__main__":
    main()
