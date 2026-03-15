from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import RecommendationRun
from ..schemas.recommendations import RecommendationRunSchema
from ..services.recommendations import (
    RecommendationRequest,
    build_recommendations,
    persist_recommendation_run,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationRequestPayload(BaseModel):
    shot_style: str = "modern_58mm"
    quantity_mode: str = "12-18 oz"
    bulk_allowed: bool = False
    allow_decaf: bool = False


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


class RecommendationResultResponse(BaseModel):
    top_result: Optional[RecommendationCandidateOut]
    alternatives: list[RecommendationCandidateOut]
    wait_recommendation: bool
    run_id: int


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
    )
    candidates = build_recommendations(db, req)
    persist_recommendation_run(db, req, candidates)
    db.commit()

    # Retrieve the newly created run
    run = db.scalar(
        select(RecommendationRun).order_by(RecommendationRun.run_at.desc()).limit(1)
    )

    top = candidates[0] if candidates else None
    alternatives = candidates[1:3]

    return RecommendationResultResponse(
        top_result=RecommendationCandidateOut(**asdict(top)) if top else None,
        alternatives=[RecommendationCandidateOut(**asdict(a)) for a in alternatives],
        wait_recommendation=not bool(candidates),
        run_id=run.id if run else 0,
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


@router.get("/{run_id}", response_model=RecommendationRunSchema)
def get_recommendation(run_id: int, db: Session = Depends(get_session)) -> RecommendationRunSchema:
    run = db.get(RecommendationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Recommendation run not found")
    return RecommendationRunSchema.model_validate(run)
