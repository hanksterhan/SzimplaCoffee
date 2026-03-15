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


_ROAST_LEVEL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("dark", ("dark roast", "dark-roast", "french roast", "italian roast", "bold roast")),
    ("medium-dark", ("espresso roast", "medium dark", "medium-dark")),
    ("medium", ("medium roast", "all-purpose", "all purpose", "balanced roast")),
    ("light-medium", ("light medium", "light-medium", "omni roast", "omni")),
    ("light", ("light roast", "filter roast", "nordic roast", "nordic")),
)

_PROCESS_FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("anaerobic", ("anaerobic", "carbonic maceration", "experimental")),
    ("wet-hulled", ("wet-hulled", "wet hulled", "semi-washed", "semi washed")),
    ("honey", ("honey", "pulped natural")),
    ("natural", ("natural", "dry process")),
    ("washed", ("washed", "wet process")),
    ("blend", ("blend",)),
)


def _normalize_origin(origin_text: str | None) -> tuple[str | None, str | None]:
    if not origin_text:
        return (None, None)
    parts = [part.strip() for part in origin_text.split(",") if part.strip()]
    if not parts:
        return (None, None)
    country = parts[0]
    region = ", ".join(parts[1:]) if len(parts) > 1 else None
    return (country, region)


def _normalize_roast_level(roast_cues: str | None) -> str:
    if not roast_cues:
        return "unknown"
    lowered = roast_cues.lower()
    for level, keywords in _ROAST_LEVEL_RULES:
        if any(keyword in lowered for keyword in keywords):
            return level
    return "unknown"


def _normalize_process_family(process_text: str | None) -> str:
    if not process_text:
        return "unknown"
    lowered = process_text.lower()
    for family, keywords in _PROCESS_FAMILY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return family
    return "unknown"


def backfill() -> None:
    session = SessionLocal()
    try:
        products = session.scalars(select(Product)).all()
        total = len(products)

        stats = {
            "parsed": 0,
            "origin": 0,
            "origin_country": 0,
            "origin_region": 0,
            "process": 0,
            "process_family": 0,
            "variety": 0,
            "roast_cues": 0,
            "roast_level": 0,
            "tasting_notes": 0,
            "espresso": 0,
            "single_origin": 0,
            "metadata": 0,
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

            if not product.origin_country:
                origin_country, origin_region = _normalize_origin(product.origin_text or parsed.origin_text)
                if origin_country:
                    product.origin_country = origin_country
                    stats["origin_country"] += 1
                    changed = True
                if not product.origin_region and origin_region:
                    product.origin_region = origin_region
                    stats["origin_region"] += 1
                    changed = True

            if not product.process_text and parsed.process_text:
                product.process_text = parsed.process_text
                stats["process"] += 1
                changed = True

            if product.process_family == "unknown":
                process_family = _normalize_process_family(product.process_text or parsed.process_text)
                if process_family != "unknown":
                    product.process_family = process_family
                    stats["process_family"] += 1
                    changed = True

            if not product.variety_text and parsed.variety_text:
                product.variety_text = parsed.variety_text
                stats["variety"] += 1
                changed = True

            if not product.roast_cues and parsed.roast_cues:
                product.roast_cues = parsed.roast_cues
                stats["roast_cues"] += 1
                changed = True

            if product.roast_level == "unknown":
                roast_level = _normalize_roast_level(product.roast_cues or parsed.roast_cues)
                if roast_level != "unknown":
                    product.roast_level = roast_level
                    stats["roast_level"] += 1
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

            if parsed.confidence > product.metadata_confidence:
                product.metadata_confidence = parsed.confidence
                stats["metadata"] += 1
                changed = True

            if parsed.confidence > 0.1 and (
                product.metadata_source == "unknown"
                or (product.metadata_source == "parser" and changed)
            ):
                product.metadata_source = "parser"
                changed = True

            if changed:
                stats["parsed"] += 1

        session.commit()

        print(
            f"\nBackfill complete.\n"
            f"  Total products:     {total}\n"
            f"  Updated:            {stats['parsed']}/{total}\n"
            f"  Origin filled:      {stats['origin']}\n"
            f"  Origin country:     {stats['origin_country']}\n"
            f"  Origin region:      {stats['origin_region']}\n"
            f"  Process filled:     {stats['process']}\n"
            f"  Process family:     {stats['process_family']}\n"
            f"  Variety filled:     {stats['variety']}\n"
            f"  Roast cues filled:  {stats['roast_cues']}\n"
            f"  Roast level:        {stats['roast_level']}\n"
            f"  Tasting notes:      {stats['tasting_notes']}\n"
            f"  Espresso flag set:  {stats['espresso']}\n"
            f"  Single origin set:  {stats['single_origin']}\n"
            f"  Metadata updates:   {stats['metadata']}\n"
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
