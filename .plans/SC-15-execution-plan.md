# SC-15 Execution Plan: /api/v1/discovery Endpoints

## Router: `backend/src/szimplacoffee/api/discovery.py`

```python
from datetime import UTC, datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Merchant, MerchantCandidate
from ..schemas.discovery import MerchantCandidateSchema
from ..services.discovery import run_discovery_pipeline

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/candidates", response_model=list[MerchantCandidateSchema])
def list_candidates(
    db: Session = Depends(get_db),
    status: str | None = Query(None),  # "pending" | "approved" | "rejected"
    limit: int = Query(100, ge=1, le=500),
) -> list[MerchantCandidateSchema]:
    q = db.query(MerchantCandidate)
    if status:
        q = q.filter(MerchantCandidate.status == status)
    else:
        q = q.filter(MerchantCandidate.status == "pending")  # default: pending
    candidates = q.order_by(MerchantCandidate.discovered_at.desc()).limit(limit).all()
    return [MerchantCandidateSchema.model_validate(c) for c in candidates]


@router.get("/candidates/{candidate_id}", response_model=MerchantCandidateSchema)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> MerchantCandidateSchema:
    c = db.query(MerchantCandidate).filter(MerchantCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return MerchantCandidateSchema.model_validate(c)


@router.post("/run", response_model=dict)
def run_discovery(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    query: str = Query("specialty coffee roaster"),
) -> dict:
    background_tasks.add_task(run_discovery_pipeline, query)
    return {"status": "started", "query": query}


@router.post("/candidates/{candidate_id}/promote", response_model=dict)
def promote_candidate(candidate_id: int, db: Session = Depends(get_db)) -> dict:
    c = db.query(MerchantCandidate).filter(MerchantCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if c.status == "approved":
        raise HTTPException(status_code=409, detail="Already promoted")

    # Check if merchant already exists
    existing = db.query(Merchant).filter(Merchant.canonical_domain == c.canonical_domain).first()
    if existing:
        c.status = "approved"
        c.reviewed_at = datetime.now(UTC)
        db.commit()
        return {"status": "promoted", "merchant_id": existing.id, "note": "merchant already existed"}

    # Create Merchant from candidate
    merchant = Merchant(
        name=c.merchant_name,
        canonical_domain=c.canonical_domain,
        homepage_url=c.homepage_url,
        platform_type=c.platform_type,
        trust_tier="candidate",
        crawl_tier="B",
    )
    db.add(merchant)
    c.status = "approved"
    c.reviewed_at = datetime.now(UTC)
    db.commit()
    db.refresh(merchant)
    return {"status": "promoted", "merchant_id": merchant.id}


@router.post("/candidates/{candidate_id}/reject", response_model=dict)
def reject_candidate(candidate_id: int, db: Session = Depends(get_db)) -> dict:
    c = db.query(MerchantCandidate).filter(MerchantCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.status = "rejected"
    c.reviewed_at = datetime.now(UTC)
    db.commit()
    return {"status": "rejected", "candidate_id": candidate_id}
```

## Test Strategy
```python
def test_list_candidates():
    resp = client.get("/api/v1/discovery/candidates")
    assert resp.status_code == 200
    # Returns pending candidates by default

def test_promote_candidate(db_with_candidate):
    resp = client.post(f"/api/v1/discovery/candidates/{candidate_id}/promote")
    assert resp.status_code == 200
    assert resp.json()["status"] == "promoted"
    # Verify Merchant was created
    merchant_resp = client.get(f"/api/v1/merchants/{resp.json()['merchant_id']}")
    assert merchant_resp.status_code == 200

def test_reject_candidate(db_with_candidate):
    resp = client.post(f"/api/v1/discovery/candidates/{candidate_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
```
