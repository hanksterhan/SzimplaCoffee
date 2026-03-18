"""DE1 Visualizer bridge — polls visualizer.coffee and imports shots as BrewFeedback."""
from __future__ import annotations

import json
import logging
import urllib.request
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import (
    DE1_AUTO_MATCH,
    DE1_DEFAULT_DOSE_GRAMS,
    VISUALIZER_API_KEY,
    VISUALIZER_USERNAME,
)
from ..models import BrewFeedback, De1BridgeState, Product, utcnow

logger = logging.getLogger(__name__)

VISUALIZER_BASE = "https://visualizer.coffee/api"
MATCH_THRESHOLD = 75.0


def _get_or_create_bridge_state(db: Session) -> De1BridgeState:
    state = db.scalar(select(De1BridgeState).limit(1))
    if state is None:
        state = De1BridgeState()
        db.add(state)
        db.flush()
    return state


def _fetch_shots(page: int = 1, per_page: int = 50) -> list[dict]:
    url = f"{VISUALIZER_BASE}/shots?username={VISUALIZER_USERNAME}&per_page={per_page}&page={page}"
    req = urllib.request.Request(url)
    if VISUALIZER_API_KEY:
        req.add_header("Authorization", f"Bearer {VISUALIZER_API_KEY}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["data"]


def _fetch_shot_detail(shot_id: str) -> dict:
    url = f"{VISUALIZER_BASE}/shots/{shot_id}"
    req = urllib.request.Request(url)
    if VISUALIZER_API_KEY:
        req.add_header("Authorization", f"Bearer {VISUALIZER_API_KEY}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _score(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio() * 100


def _fuzzy_match_product(
    db: Session, bean_brand: Optional[str], bean_type: Optional[str]
) -> Optional[int]:
    if not bean_brand and not bean_type:
        return None
    query_str = f"{bean_brand or ''} {bean_type or ''}".strip()
    products = db.scalars(select(Product)).all()
    best_id: Optional[int] = None
    best_score = 0.0
    for p in products:
        s = _score(query_str, p.name)
        if s > best_score:
            best_score = s
            best_id = p.id
    return best_id if best_score >= MATCH_THRESHOLD else None


def _parse_shot(raw: dict) -> dict:
    """Normalize a Visualizer shot detail into BrewFeedback field values."""
    data = raw.get("data") or {}

    try:
        dose = float(raw.get("bean_weight") or DE1_DEFAULT_DOSE_GRAMS)
    except (TypeError, ValueError):
        dose = float(DE1_DEFAULT_DOSE_GRAMS)
    if dose == 0:
        dose = float(DE1_DEFAULT_DOSE_GRAMS)

    try:
        yield_g: Optional[float] = float(raw.get("drink_weight") or 0) or None
    except (TypeError, ValueError):
        yield_g = None

    try:
        brew_time: Optional[float] = float(raw.get("duration") or 0) or None
    except (TypeError, ValueError):
        brew_time = None

    temp_mix = data.get("espresso_temperature_mix") or []
    try:
        water_temp: Optional[float] = float(temp_mix[0]) if temp_mix else None
    except (TypeError, ValueError, IndexError):
        water_temp = None

    return {
        "visualizer_shot_id": raw["id"],
        "dose_grams": dose,
        "yield_grams": yield_g,
        "brew_time_seconds": brew_time,
        "water_temp_c": water_temp,
        "machine": "DE1",
        "shot_style": "espresso",
        "bean_brand": raw.get("bean_brand"),
        "bean_type": raw.get("bean_type"),
    }


def run_bridge(db: Session) -> int:
    """Main entry point called by APScheduler. Returns count of shots imported."""
    if not VISUALIZER_USERNAME:
        return 0

    state = _get_or_create_bridge_state(db)
    auto_match = state.auto_match and DE1_AUTO_MATCH

    try:
        shots_list = _fetch_shots(page=1, per_page=50)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DE1 bridge: failed to fetch shots list: %s", exc)
        state.last_poll_at = utcnow()
        db.commit()
        return 0

    imported = 0
    first_new_id: Optional[str] = None

    for shot_summary in shots_list:
        shot_id = shot_summary["id"]
        if shot_id == state.last_seen_shot_id:
            break

        existing = db.scalar(
            select(BrewFeedback).where(BrewFeedback.visualizer_shot_id == shot_id)
        )
        if existing:
            continue

        try:
            raw = _fetch_shot_detail(shot_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DE1 bridge: failed to fetch shot %s: %s", shot_id, exc)
            continue

        parsed = _parse_shot(raw)

        product_id: Optional[int] = None
        if auto_match:
            product_id = _fuzzy_match_product(
                db, parsed.get("bean_brand"), parsed.get("bean_type")
            )
            if product_id:
                logger.info(
                    "DE1 bridge: matched shot %s → product_id=%d", shot_id, product_id
                )

        fb = BrewFeedback(
            purchase_id=None,
            shot_style=parsed["shot_style"],
            machine=parsed["machine"],
            dose_grams=parsed["dose_grams"],
            yield_grams=parsed["yield_grams"],
            brew_time_seconds=parsed["brew_time_seconds"],
            water_temp_c=parsed["water_temp_c"],
            product_id=product_id,
            visualizer_shot_id=shot_id,
            rating=0.0,
            would_rebuy=True,
            difficulty_score=0.5,
        )
        db.add(fb)
        imported += 1

        if first_new_id is None:
            first_new_id = shot_id

    if first_new_id is not None:
        state.last_seen_shot_id = first_new_id
    state.last_poll_at = utcnow()
    state.shots_imported = (state.shots_imported or 0) + imported
    db.commit()

    logger.info("DE1 bridge: imported %d new shots", imported)
    return imported
