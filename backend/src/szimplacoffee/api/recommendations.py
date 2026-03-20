from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import RecommendationRun
from ..schemas.recommendations import RecommendationRunSchema
from ..services.recommendations import (
    RecommendationRequest,
    build_biggest_sales,
    build_recommendations,
    build_wait_assessment,
    persist_recommendation_run,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationRequestPayload(BaseModel):
    shot_style: str = "modern_58mm"
    quantity_mode: str = "12-18 oz"
    bulk_allowed: bool = False
    allow_decaf: bool = False
    current_inventory_grams: int = 0  # SC-56
    explain_scores: bool = False  # SC-67


class ScoreBreakdown(BaseModel):
    """Score component breakdown returned when explain_scores=True."""

    merchant_score: float
    quantity_score: float
    espresso_score: float
    deal_score: float
    freshness_score: float
    history_score: float
    promo_bonus: float
    brew_avg_rating: Optional[float] = None
    brew_session_count: int = 0
    brew_boost: float = 0.0
    brew_penalty: float
    total: float
    weights: dict[str, float]


class RecommendationCandidateOut(BaseModel):
    merchant_name: str
    product_name: str
    variant_label: str
    product_url: str
    image_url: str
    weight_grams: Optional[int]
    landed_price_cents: int
    landed_price_per_oz_cents: Optional[int]
    best_promo_label: Optional[str]
    discounted_landed_price_cents: Optional[int]
    score: float
    pros: list[str]
    brew_session_count: int = 0
    score_breakdown: Optional[ScoreBreakdown] = None  # SC-67: populated when explain_scores=True
    # SC-109: Baseline deal intelligence
    deal_score: Optional[float] = None
    deal_badge: Optional[str] = None
    # SC-112: Template-based explanation of ranking
    why_text: str = ""


class FilteredCandidateOut(BaseModel):  # SC-67
    merchant_name: str
    product_name: str
    variant_label: str
    filter_reason: str


class RecommendationResultResponse(BaseModel):
    top_result: Optional[RecommendationCandidateOut]
    alternatives: list[RecommendationCandidateOut]
    wait_recommendation: bool
    wait_rationale: Optional[str] = None  # SC-54
    run_id: int
    filtered_candidates: Optional[list[FilteredCandidateOut]] = None  # SC-67: populated when explain_scores=True


class BiggestSaleCandidateOut(BaseModel):
    merchant_name: str
    product_name: str
    variant_label: str
    product_url: str
    image_url: str
    weight_grams: Optional[int]
    current_price_cents: int
    landed_price_cents: int
    landed_price_per_oz_cents: Optional[int]
    compare_at_discount_percent: float
    price_drop_7d_percent: float
    price_drop_30d_percent: float
    historical_low_cents: int
    best_promo_label: Optional[str]
    discounted_landed_price_cents: Optional[int]
    score: float
    reasons: list[str]


@router.post("", response_model=RecommendationResultResponse, status_code=201)
def create_recommendation(
    payload: RecommendationRequestPayload,
    db: Session = Depends(get_session),
) -> RecommendationResultResponse:
    req = RecommendationRequest(
        shot_style=payload.shot_style,  # type: ignore[arg-type]
        quantity_mode=payload.quantity_mode,  # type: ignore[arg-type]
        bulk_allowed=payload.bulk_allowed,
        allow_decaf=payload.allow_decaf,
        current_inventory_grams=payload.current_inventory_grams,
        explain_scores=payload.explain_scores,
    )
    candidates, filtered = build_recommendations(db, req)
    persist_recommendation_run(db, req, candidates)
    db.commit()

    # Retrieve the newly created run
    run = db.scalar(
        select(RecommendationRun).order_by(RecommendationRun.run_at.desc()).limit(1)
    )

    top = candidates[0] if candidates else None
    alternatives = candidates[1:3]
    wait, wait_rationale = build_wait_assessment(candidates, no_candidates=not bool(candidates), current_inventory_grams=payload.current_inventory_grams)

    filtered_out: list[FilteredCandidateOut] | None = None
    if payload.explain_scores:
        filtered_out = [FilteredCandidateOut(**asdict(f)) for f in filtered]

    return RecommendationResultResponse(
        top_result=RecommendationCandidateOut(**asdict(top)) if top else None,
        alternatives=[RecommendationCandidateOut(**asdict(a)) for a in alternatives],
        wait_recommendation=wait,
        wait_rationale=wait_rationale,
        run_id=run.id if run else 0,
        filtered_candidates=filtered_out,
    )


@router.get("", response_model=list[RecommendationRunSchema])
def list_recommendations(
    db: Session = Depends(get_session),
    limit: int = Query(20, ge=1, le=100),
) -> list[RecommendationRunSchema]:
    runs = db.scalars(
        select(RecommendationRun)
        .order_by(RecommendationRun.run_at.desc())
        .limit(limit)
    ).all()
    return [RecommendationRunSchema.model_validate(r) for r in runs]


@router.get("/today", response_model=dict)
def today_buying_brief(
    db: Session = Depends(get_session),
    shot_style: str = Query("modern_58mm"),
    quantity_mode: str = Query("12-18 oz"),
    limit: int = Query(5, ge=1, le=20),
    current_inventory_grams: int = Query(0, ge=0),
) -> dict:
    """SC-52: Return a Today buying brief — best current option + notable sales.

    This is designed for the daily utility dashboard: single call answers
    'what should I buy today?' without requiring a full recommendation run.
    """
    req = RecommendationRequest(
        shot_style=shot_style,  # type: ignore[arg-type]
        quantity_mode=quantity_mode,  # type: ignore[arg-type]
        bulk_allowed=False,
        allow_decaf=False,
        current_inventory_grams=current_inventory_grams,
    )
    candidates, _ = build_recommendations(db, req)
    sales = build_biggest_sales(db, limit=limit)

    top = candidates[0] if candidates else None
    alternatives = candidates[1:3]

    wait, wait_rationale = build_wait_assessment(candidates, no_candidates=not bool(candidates), current_inventory_grams=current_inventory_grams)
    return {
        "has_recommendation": bool(top) and not wait,
        "top_pick": asdict(top) if top else None,
        "alternatives": [asdict(a) for a in alternatives],
        "notable_sales": [asdict(s) for s in sales[:limit]],
        "shot_style": shot_style,
        "quantity_mode": quantity_mode,
        "wait_recommendation": wait,
        "wait_rationale": wait_rationale,
    }


@router.get("/biggest-sales", response_model=list[BiggestSaleCandidateOut])
def biggest_sales_today(
    db: Session = Depends(get_session),
    limit: int = Query(10, ge=1, le=50),
) -> list[BiggestSaleCandidateOut]:
    candidates = build_biggest_sales(db, limit=limit)
    return [BiggestSaleCandidateOut(**asdict(candidate)) for candidate in candidates]


@router.get("/{run_id}", response_model=RecommendationRunSchema)
def get_recommendation(run_id: int, db: Session = Depends(get_session)) -> RecommendationRunSchema:
    run = db.get(RecommendationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Recommendation run not found")
    return RecommendationRunSchema.model_validate(run)
