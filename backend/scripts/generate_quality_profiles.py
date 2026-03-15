"""SC-32: Generate quality profiles for all merchants and print a summary."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy import select
from szimplacoffee.db import session_scope
from szimplacoffee.models import MerchantQualityProfile
from szimplacoffee.services.quality_scorer import score_all_merchants


def main() -> None:
    print("=== SC-32: Generating Merchant Quality Profiles ===\n")

    with session_scope() as session:
        # Capture before state
        existing = {
            row.merchant_id: row.overall_quality_score
            for row in session.scalars(select(MerchantQualityProfile)).all()
        }

        results = score_all_merchants(session)
        session.commit()

        # Print summary table
        header = (
            f"{'ID':>4}  {'Merchant':<30}  {'Fresh':>6}  {'Ship':>6}  "
            f"{'Meta':>6}  {'Esp':>6}  {'Svc':>6}  {'Overall':>8}  {'Change':>8}"
        )
        print(header)
        print("-" * len(header))

        for row in sorted(results, key=lambda r: r["overall"], reverse=True):
            prev = existing.get(row["merchant_id"])
            if prev is not None:
                delta = row["overall"] - prev
                change_str = f"{delta:+.4f}"
            else:
                change_str = "   NEW"

            print(
                f"{row['merchant_id']:>4}  {row['name']:<30}  "
                f"{row['freshness']:>6.4f}  {row['shipping']:>6.4f}  "
                f"{row['metadata']:>6.4f}  {row['espresso']:>6.4f}  "
                f"{row['service']:>6.4f}  {row['overall']:>8.4f}  {change_str:>8}"
            )

        print(f"\n✅ Quality profiles generated for {len(results)} merchants.")
        new_count = sum(1 for r in results if r["merchant_id"] not in existing)
        upd_count = len(results) - new_count
        print(f"   {new_count} new profiles created, {upd_count} updated.")


if __name__ == "__main__":
    main()
