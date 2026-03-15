"""Backfill existing products with parsed coffee metadata (SC-31).

Usage:
    cd /home/h6nk/SzimplaCoffee/backend
    PYTHONPATH=src uv run python3 scripts/backfill_product_metadata.py

For each product in the database:
  1. Read existing name (and description_html if stored).
  2. Run parse_coffee_metadata().
  3. Update product fields where parsed confidence > 0 AND the field is currently empty.
  4. Print summary stats.
"""
from __future__ import annotations

import sys

from sqlalchemy import select

from szimplacoffee.db import SessionLocal
from szimplacoffee.models import Product
from szimplacoffee.services.coffee_parser import parse_coffee_metadata


def backfill() -> None:
    session = SessionLocal()
    try:
        products = session.scalars(select(Product)).all()
        total = len(products)

        stats = {
            "parsed": 0,
            "origin": 0,
            "process": 0,
            "variety": 0,
            "roast_cues": 0,
            "tasting_notes": 0,
            "espresso": 0,
            "single_origin": 0,
        }

        for product in products:
            # Use name only — products currently don't store body_html
            # The parser handles name-only mode with lower confidence ceiling
            parsed = parse_coffee_metadata(product.name, "")

            # Only update fields that are currently empty
            changed = False

            if not product.origin_text and parsed.origin_text:
                product.origin_text = parsed.origin_text
                stats["origin"] += 1
                changed = True

            if not product.process_text and parsed.process_text:
                product.process_text = parsed.process_text
                stats["process"] += 1
                changed = True

            if not product.variety_text and parsed.variety_text:
                product.variety_text = parsed.variety_text
                stats["variety"] += 1
                changed = True

            if not product.roast_cues and parsed.roast_cues:
                product.roast_cues = parsed.roast_cues
                stats["roast_cues"] += 1
                changed = True

            if not product.tasting_notes_text and parsed.tasting_notes_text:
                product.tasting_notes_text = parsed.tasting_notes_text
                stats["tasting_notes"] += 1
                changed = True

            # Flags: only promote from False → True (never demote)
            if not product.is_espresso_recommended and parsed.is_espresso_recommended:
                product.is_espresso_recommended = True
                stats["espresso"] += 1
                changed = True

            if not product.is_single_origin and parsed.is_single_origin:
                product.is_single_origin = True
                stats["single_origin"] += 1
                changed = True

            if changed:
                stats["parsed"] += 1

        session.commit()

        print(
            f"\nBackfill complete.\n"
            f"  Total products:     {total}\n"
            f"  Updated:            {stats['parsed']}/{total}\n"
            f"  Origin filled:      {stats['origin']}\n"
            f"  Process filled:     {stats['process']}\n"
            f"  Variety filled:     {stats['variety']}\n"
            f"  Roast cues filled:  {stats['roast_cues']}\n"
            f"  Tasting notes:      {stats['tasting_notes']}\n"
            f"  Espresso flag set:  {stats['espresso']}\n"
            f"  Single origin set:  {stats['single_origin']}\n"
        )

        # Summary line as requested in ticket
        print(
            f"Parsed {stats['parsed']}/{total} products. "
            f"Origin: {stats['origin']}, "
            f"Process: {stats['process']}, "
            f"Tasting: {stats['tasting_notes']}, "
            f"Espresso: {stats['espresso']}"
        )
    except Exception as exc:
        session.rollback()
        print(f"Backfill failed: {exc}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    backfill()
