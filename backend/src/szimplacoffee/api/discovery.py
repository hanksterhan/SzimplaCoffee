from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session, session_scope
from ..models import Merchant, MerchantCandidate
from ..schemas.discovery import MerchantCandidateSchema
from ..services.discovery import promote_candidate, run_discovery

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _background_discovery(query: str) -> None:
    try:
        with session_scope() as session:
            run_discovery(session, queries=[query])
    except Exception:
        return


@router.get("/candidates", response_model=list[MerchantCandidateSchema])
def list_candidates(
    db: Session = Depends(get_session),
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(100, ge=1, le=500),
) -> list[MerchantCandidateSchema]:
    q = select(MerchantCandidate)
    if status:
        q = q.where(MerchantCandidate.status == status)
    else:
        q = q.where(MerchantCandidate.status == "pending")
    q = q.order_by(MerchantCandidate.discovered_at.desc()).limit(limit)
    candidates = db.scalars(q).all()
    return [MerchantCandidateSchema.model_validate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=MerchantCandidateSchema)
def get_candidate(candidate_id: int, db: Session = Depends(get_session)) -> MerchantCandidateSchema:
    c = db.get(MerchantCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return MerchantCandidateSchema.model_validate(c)


@router.post("/run", response_model=dict)
def run_discovery_endpoint(
    background_tasks: BackgroundTasks,
    query: str = Query("specialty coffee roaster"),
) -> dict:
    background_tasks.add_task(_background_discovery, query)
    return {"status": "started", "query": query}


@router.post("/candidates/{candidate_id}/promote", response_model=dict)
def promote_candidate_endpoint(
    candidate_id: int,
    db: Session = Depends(get_session),
) -> dict:
    c = db.get(MerchantCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if c.status == "approved":
        raise HTTPException(status_code=409, detail="Candidate already promoted")

    # Check if merchant already exists for this domain
    existing = db.scalar(
        select(Merchant).where(Merchant.canonical_domain == c.canonical_domain)
    )
    if existing:
        c.status = "approved"
        db.commit()
        return {"status": "promoted", "merchant_id": existing.id, "note": "merchant already existed"}

    merchant = promote_candidate(db, c)
    db.commit()
    return {"status": "promoted", "merchant_id": merchant.id}


@router.post("/candidates/{candidate_id}/reject", response_model=dict)
def reject_candidate_endpoint(
    candidate_id: int,
    db: Session = Depends(get_session),
) -> dict:
    c = db.get(MerchantCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.status = "rejected"
    db.commit()
    return {"status": "rejected", "candidate_id": candidate_id}
