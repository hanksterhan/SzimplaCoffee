# SC-12 Execution Plan: /api/v1/merchants Endpoints

## Router: `backend/src/szimplacoffee/api/merchants.py`

```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import CrawlRun, Merchant, ShippingPolicy
from ..schemas.common import PaginatedResponse
from ..schemas.crawls import CrawlRunSchema
from ..schemas.merchants import MerchantCreate, MerchantDetail, MerchantSummary
from ..services.crawlers import run_crawl_for_merchant

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.get("", response_model=PaginatedResponse[MerchantSummary])
def list_merchants(
    db: Session = Depends(get_db),
    platform_type: str | None = Query(None),
    trust_tier: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[MerchantSummary]:
    q = db.query(Merchant)
    if platform_type:
        q = q.filter(Merchant.platform_type == platform_type)
    if trust_tier:
        q = q.filter(Merchant.trust_tier == trust_tier)
    if is_active is not None:
        q = q.filter(Merchant.is_active == is_active)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[MerchantSummary.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
    )


@router.get("/{merchant_id}", response_model=MerchantDetail)
def get_merchant(merchant_id: int, db: Session = Depends(get_db)) -> MerchantDetail:
    m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return MerchantDetail.model_validate(m)


@router.post("", response_model=MerchantSummary, status_code=201)
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db)) -> MerchantSummary:
    m = Merchant(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return MerchantSummary.model_validate(m)


@router.post("/{merchant_id}/crawl", response_model=dict)
def trigger_crawl(
    merchant_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    run = CrawlRun(
        merchant_id=merchant_id,
        run_type="manual",
        adapter_name=m.platform_type,
        status="started",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(run_crawl_for_merchant, merchant_id, run.id)
    return {"crawl_run_id": run.id, "status": "started"}


@router.get("/{merchant_id}/crawl/{run_id}", response_model=CrawlRunSchema)
def poll_crawl(merchant_id: int, run_id: int, db: Session = Depends(get_db)) -> CrawlRunSchema:
    run = db.query(CrawlRun).filter(
        CrawlRun.id == run_id,
        CrawlRun.merchant_id == merchant_id,
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Crawl run not found")
    return CrawlRunSchema.model_validate(run)


@router.get("/{merchant_id}/crawl-runs", response_model=list[CrawlRunSchema])
def list_crawl_runs(merchant_id: int, db: Session = Depends(get_db)) -> list[CrawlRunSchema]:
    runs = (
        db.query(CrawlRun)
        .filter(CrawlRun.merchant_id == merchant_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(50)
        .all()
    )
    return [CrawlRunSchema.model_validate(r) for r in runs]
```

## Mount in `main.py`
```python
from .api.merchants import router as merchants_router

# After existing app = FastAPI(...)
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(merchants_router)
app.include_router(api_v1)
```

## MerchantCreate schema (add to merchants.py)
```python
class MerchantCreate(BaseModel):
    name: str
    canonical_domain: str
    homepage_url: str
    platform_type: str = "unknown"
    country_code: str = "US"
    crawl_tier: str = "B"
    trust_tier: str = "candidate"
```

## Test pattern (`tests/test_api_merchants.py`)
```python
from fastapi.testclient import TestClient
from szimplacoffee.main import app

client = TestClient(app)

def test_list_merchants():
    resp = client.get("/api/v1/merchants")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 16  # DB has 16

def test_merchant_detail():
    resp = client.get("/api/v1/merchants/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "shipping_policies" in data
    assert "quality_profile" in data

def test_trigger_crawl():
    resp = client.post("/api/v1/merchants/1/crawl")
    assert resp.status_code == 200
    assert "crawl_run_id" in resp.json()

def test_poll_crawl():
    trigger = client.post("/api/v1/merchants/1/crawl").json()
    run_id = trigger["crawl_run_id"]
    resp = client.get(f"/api/v1/merchants/1/crawl/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("started", "completed", "failed")
```
