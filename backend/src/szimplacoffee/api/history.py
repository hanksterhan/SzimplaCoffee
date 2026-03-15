from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_session
from ..models import BrewFeedback, Merchant, PurchaseHistory
from ..schemas.history import (
    BrewFeedbackCreate,
    BrewFeedbackOut,
    BrewFeedbackUpdate,
    PurchaseCreate,
    PurchaseDetail,
    PurchaseStats,
    PurchaseSummary,
    PurchaseUpdate,
)

router = APIRouter(tags=["purchases"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _to_summary(p: PurchaseHistory) -> PurchaseSummary:
    return PurchaseSummary(
        id=p.id,
        merchant_id=p.merchant_id,
        product_name=p.product_name,
        origin_text=p.origin_text,
        process_text=p.process_text,
        price_cents=p.price_cents,
        weight_grams=p.weight_grams,
        purchased_at=p.purchased_at,
        source_system=p.source_system,
        source_ref=p.source_ref,
        feedback_count=len(p.brew_feedback),
    )


# ── Purchase CRUD ────────────────────────────────────────────────────────────

@router.post("/purchases", response_model=PurchaseDetail, status_code=201)
def create_purchase(
    body: PurchaseCreate,
    db: Session = Depends(get_session),
) -> PurchaseDetail:
    merchant = db.get(Merchant, body.merchant_id)
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    p = PurchaseHistory(
        merchant_id=body.merchant_id,
        product_name=body.product_name,
        origin_text=body.origin_text,
        process_text=body.process_text,
        price_cents=body.price_cents,
        weight_grams=body.weight_grams,
        purchased_at=body.purchased_at or datetime.now(UTC),
        source_system=body.source_system,
        source_ref=body.source_ref,
    )
    db.add(p)
    db.flush()
    db.refresh(p)
    return PurchaseDetail.model_validate(p)


@router.get("/purchases", response_model=list[PurchaseSummary])
def list_purchases(
    merchant_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_session),
) -> list[PurchaseSummary]:
    q = (
        select(PurchaseHistory)
        .options(selectinload(PurchaseHistory.brew_feedback))
        .order_by(PurchaseHistory.purchased_at.desc())
    )
    if merchant_id is not None:
        q = q.where(PurchaseHistory.merchant_id == merchant_id)
    if date_from is not None:
        q = q.where(PurchaseHistory.purchased_at >= date_from)
    if date_to is not None:
        q = q.where(PurchaseHistory.purchased_at <= date_to)
    items = db.scalars(q).all()
    return [_to_summary(p) for p in items]


@router.get("/purchases/stats", response_model=PurchaseStats)
def purchase_stats(db: Session = Depends(get_session)) -> PurchaseStats:
    rows = db.scalars(
        select(PurchaseHistory).options(selectinload(PurchaseHistory.brew_feedback))
    ).all()
    if not rows:
        return PurchaseStats(
            total_purchases=0,
            total_spent_cents=0,
            avg_price_per_lb_cents=0.0,
            favorite_merchant_id=None,
            favorite_merchant_name=None,
        )

    total_purchases = len(rows)
    total_spent_cents = sum(r.price_cents for r in rows)

    # avg price per lb (453.6g per lb)
    price_per_lb_values = [
        r.price_cents / (r.weight_grams / 453.6) for r in rows if r.weight_grams > 0
    ]
    avg_price_per_lb_cents = (
        sum(price_per_lb_values) / len(price_per_lb_values) if price_per_lb_values else 0.0
    )

    # favorite merchant by count
    from collections import Counter

    merchant_counts = Counter(r.merchant_id for r in rows)
    fav_merchant_id = merchant_counts.most_common(1)[0][0] if merchant_counts else None
    fav_merchant_name: Optional[str] = None
    if fav_merchant_id is not None:
        m = db.get(Merchant, fav_merchant_id)
        fav_merchant_name = m.name if m else None

    return PurchaseStats(
        total_purchases=total_purchases,
        total_spent_cents=total_spent_cents,
        avg_price_per_lb_cents=avg_price_per_lb_cents,
        favorite_merchant_id=fav_merchant_id,
        favorite_merchant_name=fav_merchant_name,
    )


@router.get("/purchases/{purchase_id}", response_model=PurchaseDetail)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_session),
) -> PurchaseDetail:
    p = db.scalar(
        select(PurchaseHistory)
        .options(selectinload(PurchaseHistory.brew_feedback))
        .where(PurchaseHistory.id == purchase_id)
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return PurchaseDetail.model_validate(p)


@router.put("/purchases/{purchase_id}", response_model=PurchaseDetail)
def update_purchase(
    purchase_id: int,
    body: PurchaseUpdate,
    db: Session = Depends(get_session),
) -> PurchaseDetail:
    p = db.scalar(
        select(PurchaseHistory)
        .options(selectinload(PurchaseHistory.brew_feedback))
        .where(PurchaseHistory.id == purchase_id)
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.flush()
    db.refresh(p)
    return PurchaseDetail.model_validate(p)


@router.delete("/purchases/{purchase_id}", status_code=204)
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_session),
) -> None:
    p = db.get(PurchaseHistory, purchase_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    db.delete(p)


# ── Brew Feedback ─────────────────────────────────────────────────────────────

@router.post("/purchases/{purchase_id}/feedback", response_model=BrewFeedbackOut, status_code=201)
def create_feedback(
    purchase_id: int,
    body: BrewFeedbackCreate,
    db: Session = Depends(get_session),
) -> BrewFeedbackOut:
    p = db.get(PurchaseHistory, purchase_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    fb = BrewFeedback(
        purchase_id=purchase_id,
        shot_style=body.shot_style,
        grinder=body.grinder,
        basket=body.basket,
        rating=body.rating,
        would_rebuy=body.would_rebuy,
        difficulty_score=body.difficulty_score,
        notes=body.notes,
    )
    db.add(fb)
    db.flush()
    db.refresh(fb)
    return BrewFeedbackOut.model_validate(fb)


@router.get("/purchases/{purchase_id}/feedback", response_model=list[BrewFeedbackOut])
def list_feedback(
    purchase_id: int,
    db: Session = Depends(get_session),
) -> list[BrewFeedbackOut]:
    p = db.get(PurchaseHistory, purchase_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    items = db.scalars(
        select(BrewFeedback).where(BrewFeedback.purchase_id == purchase_id)
    ).all()
    return [BrewFeedbackOut.model_validate(fb) for fb in items]


@router.put("/feedback/{feedback_id}", response_model=BrewFeedbackOut)
def update_feedback(
    feedback_id: int,
    body: BrewFeedbackUpdate,
    db: Session = Depends(get_session),
) -> BrewFeedbackOut:
    fb = db.get(BrewFeedback, feedback_id)
    if fb is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(fb, field, value)
    db.flush()
    db.refresh(fb)
    return BrewFeedbackOut.model_validate(fb)


@router.delete("/feedback/{feedback_id}", status_code=204)
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_session),
) -> None:
    fb = db.get(BrewFeedback, feedback_id)
    if fb is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    db.delete(fb)
