# SC-14 Execution Plan: /api/v1/recommendations Endpoints

## First: Read services/recommendations.py to understand the engine interface
The recommendation engine in `services/recommendations.py` has a scoring function. Inspect it to understand:
- Input parameters: shot_style, bag_size_grams, budget_cents
- Output: ranked list of scored products with rationale
- How it writes to recommendation_runs table

## Router: `backend/src/szimplacoffee/api/recommendations.py`

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import RecommendationRun
from ..schemas.recommendations import RecommendationRunSchema
from ..services.recommendations import run_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationRequest(BaseModel):
    shot_style: str = "espresso"       # "espresso" | "filter" | "omni"
    bag_size_grams: int = 340          # 340 (12oz) or 2268 (5lb)
    budget_cents: int | None = None    # None = no limit
    trust_tier_filter: str | None = None  # "trusted" | None = all


class RecommendationResult(BaseModel):
    run_id: int
    top_result: dict
    alternatives: list[dict]
    wait_recommendation: bool


@router.post("", response_model=RecommendationResult, status_code=201)
def create_recommendation(
    req: RecommendationRequest,
    db: Session = Depends(get_db),
) -> RecommendationResult:
    result = run_recommendations(
        db=db,
        shot_style=req.shot_style,
        bag_size_grams=req.bag_size_grams,
        budget_cents=req.budget_cents,
        trust_tier_filter=req.trust_tier_filter,
    )
    # run_recommendations saves to DB and returns run_id + results
    return RecommendationResult(
        run_id=result["run_id"],
        top_result=result["top_result"],
        alternatives=result["alternatives"],
        wait_recommendation=result.get("wait_recommendation", False),
    )


@router.get("/{run_id}", response_model=RecommendationRunSchema)
def get_recommendation(run_id: int, db: Session = Depends(get_db)) -> RecommendationRunSchema:
    run = db.query(RecommendationRun).filter(RecommendationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Recommendation run not found")
    return RecommendationRunSchema.model_validate(run)


@router.get("", response_model=list[RecommendationRunSchema])
def list_recommendations(
    db: Session = Depends(get_db),
    limit: int = 20,
) -> list[RecommendationRunSchema]:
    runs = (
        db.query(RecommendationRun)
        .order_by(RecommendationRun.run_at.desc())
        .limit(limit)
        .all()
    )
    return [RecommendationRunSchema.model_validate(r) for r in runs]
```

## Enrich `RecommendationRunSchema` with parsed fields

```python
# In schemas/recommendations.py
class RecommendationRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_at: datetime
    request_json: str
    top_result_json: str
    alternatives_json: str
    wait_recommendation: bool
    model_version: str

    @computed_field
    @property
    def request(self) -> dict:
        return json.loads(self.request_json or "{}")

    @computed_field
    @property
    def top_result(self) -> dict:
        return json.loads(self.top_result_json or "{}")

    @computed_field
    @property
    def alternatives(self) -> list[dict]:
        return json.loads(self.alternatives_json or "[]")
```

## Known Data
- 7 existing recommendation runs in DB
- request_json contains: shot_style, bag_size, budget, trust_tier_filter params
- top_result_json / alternatives_json: scored product data with rationale field
- wait_recommendation: bool suggesting "wait for sale" rather than buying now

## Test Strategy
```python
def test_create_recommendation():
    resp = client.post("/api/v1/recommendations", json={
        "shot_style": "espresso",
        "bag_size_grams": 340,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "run_id" in data
    assert "top_result" in data

def test_list_recommendations():
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 200
    assert len(resp.json()) >= 7  # 7 in DB
```
