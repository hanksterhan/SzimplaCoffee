from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session, session_scope
from ..models import CrawlRun, Merchant
from ..schemas.common import PaginatedResponse
from ..schemas.crawls import CrawlRunSchema
from ..schemas.merchants import MerchantDetail, MerchantSummary
from ..schemas.promos import MerchantPromoSchema
from ..models import MerchantPromo
from ..services.crawlers import crawl_merchant
from ..services.platforms import detect_platform, recommended_crawl_tier
from ..services.quality_scorer import score_merchant
from ..services.discovery import meets_buying_threshold, BUYING_QUALITY_FLOOR, BUYING_VIEW_TRUSTED_TIERS, CATALOG_VIEW_TIERS

router = APIRouter(prefix="/merchants", tags=["merchants"])


class MerchantCreateRequest(BaseModel):
    url: str
    trust_tier: str = "candidate"


def _background_crawl(merchant_id: int, run_id: int) -> None:
    try:
        with session_scope() as session:
            merchant = session.get(Merchant, merchant_id)
            run = session.get(CrawlRun, run_id)
            if merchant is None or run is None:
                return
            crawl_merchant(session, merchant, run=run)
    except Exception:
        return


def _enqueue_crawl(session: Session, merchant: Merchant) -> tuple[CrawlRun, bool]:
    latest_run = session.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant.id)
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    if latest_run and latest_run.status in {"queued", "started"}:
        return latest_run, False
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name=merchant.platform_type,
        status="queued",
        confidence=0.0,
        records_written=0,
    )
    session.add(run)
    session.flush()
    return run, True


@router.get("", response_model=PaginatedResponse[MerchantSummary])
def list_merchants(
    db: Session = Depends(get_session),
    platform_type: str | None = Query(None),
    trust_tier: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[MerchantSummary]:
    q = select(Merchant)
    if platform_type:
        q = q.where(Merchant.platform_type == platform_type)
    if trust_tier:
        q = q.where(Merchant.trust_tier == trust_tier)
    if is_active is not None:
        q = q.where(Merchant.is_active == is_active)
    total = len(db.scalars(q).all())
    items = db.scalars(q.offset((page - 1) * page_size).limit(page_size)).all()
    return PaginatedResponse(
        items=[MerchantSummary.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
    )


@router.get("/{merchant_id}", response_model=MerchantDetail)
def get_merchant(merchant_id: int, db: Session = Depends(get_session)) -> MerchantDetail:
    m = db.get(Merchant, merchant_id)
    if not m:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return MerchantDetail.model_validate(m)


@router.post("", response_model=MerchantSummary, status_code=201)
def create_merchant(
    payload: MerchantCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
) -> MerchantSummary:
    detection = detect_platform(payload.url)
    existing = db.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
    if existing:
        return MerchantSummary.model_validate(existing)

    merchant = Merchant(
        name=detection.merchant_name,
        canonical_domain=detection.domain,
        homepage_url=detection.normalized_url,
        platform_type=detection.platform_type,
        crawl_tier=recommended_crawl_tier(detection.platform_type, detection.confidence),
        trust_tier=payload.trust_tier,
    )
    db.add(merchant)
    db.flush()
    run, should_schedule = _enqueue_crawl(db, merchant)
    db.commit()
    if should_schedule:
        background_tasks.add_task(_background_crawl, merchant.id, run.id)
    return MerchantSummary.model_validate(merchant)


@router.post("/{merchant_id}/crawl", response_model=dict)
def trigger_crawl(
    merchant_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
) -> dict:
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    run, should_schedule = _enqueue_crawl(db, merchant)
    db.commit()
    if should_schedule:
        background_tasks.add_task(_background_crawl, merchant_id, run.id)
    return {"status": "started", "crawl_run_id": run.id}


@router.get("/{merchant_id}/status", response_model=CrawlRunSchema)
def get_merchant_status(merchant_id: int, db: Session = Depends(get_session)) -> CrawlRunSchema:
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    run = db.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    if not run:
        raise HTTPException(status_code=404, detail="No crawl runs found for this merchant")
    return CrawlRunSchema.model_validate(run)


@router.get("/{merchant_id}/crawl-runs", response_model=list[CrawlRunSchema])
def list_crawl_runs(merchant_id: int, db: Session = Depends(get_session)) -> list[CrawlRunSchema]:
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    runs = db.scalars(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(50)
    ).all()
    return [CrawlRunSchema.model_validate(r) for r in runs]


@router.post("/{merchant_id}/refresh-quality", response_model=dict)
def refresh_quality(
    merchant_id: int,
    db: Session = Depends(get_session),
) -> dict:
    """SC-32: Re-compute and upsert quality profile for a single merchant."""
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    profile = score_merchant(db, merchant)
    db.commit()
    return {
        "merchant_id": merchant_id,
        "overall_quality_score": profile.overall_quality_score,
        "freshness_transparency_score": profile.freshness_transparency_score,
        "shipping_clarity_score": profile.shipping_clarity_score,
        "metadata_quality_score": profile.metadata_quality_score,
        "espresso_relevance_score": profile.espresso_relevance_score,
        "service_confidence_score": profile.service_confidence_score,
        "last_reviewed_at": profile.last_reviewed_at.isoformat() if profile.last_reviewed_at else None,
    }


@router.get("/{merchant_id}/crawl-quality", response_model=dict)
def get_crawl_quality(
    merchant_id: int,
    db: Session = Depends(get_session),
) -> dict:
    """Return crawl-quality metrics for the most recent completed crawl run (SC-51)."""
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    run = db.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant_id, CrawlRun.status == "completed")
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    if not run:
        return {
            "merchant_id": merchant_id,
            "has_completed_crawl": False,
            "crawl_quality_score": 0.0,
            "catalog_strategy": "none",
            "promo_strategy": "none",
            "shipping_strategy": "none",
            "metadata_strategy": "none",
            "adapter_name": None,
            "records_written": 0,
            "confidence": 0.0,
            "finished_at": None,
        }
    return {
        "merchant_id": merchant_id,
        "has_completed_crawl": True,
        "crawl_quality_score": run.crawl_quality_score,
        "catalog_strategy": run.catalog_strategy,
        "promo_strategy": run.promo_strategy,
        "shipping_strategy": run.shipping_strategy,
        "metadata_strategy": run.metadata_strategy,
        "adapter_name": run.adapter_name,
        "records_written": run.records_written,
        "confidence": run.confidence,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/low-confidence", response_model=list[MerchantSummary])
def list_low_confidence_merchants(
    db: Session = Depends(get_session),
    max_quality_score: float = Query(0.5, ge=0.0, le=1.0),
    page_size: int = Query(50, ge=1, le=200),
) -> list[MerchantSummary]:
    """List merchants with low crawl quality — for the review queue (SC-51/SC-52)."""
    # Find merchant IDs with recent completed runs having low quality scores
    subq = (
        select(CrawlRun.merchant_id)
        .where(CrawlRun.status == "completed", CrawlRun.crawl_quality_score <= max_quality_score)
        .distinct()
    )
    low_confidence_ids = db.scalars(subq).all()
    if not low_confidence_ids:
        return []
    merchants = db.scalars(
        select(Merchant)
        .where(Merchant.id.in_(low_confidence_ids), Merchant.is_active.is_(True))
        .limit(page_size)
    ).all()
    return [MerchantSummary.model_validate(m) for m in merchants]


@router.get("/registry-summary", response_model=dict)
def get_registry_summary(
    db: Session = Depends(get_session),
) -> dict:
    """SC-53: Registry health summary — tier distribution, buying-eligible count."""
    all_merchants = db.scalars(select(Merchant).where(Merchant.is_active.is_(True))).all()
    tier_dist: dict[str, int] = {}
    trust_dist: dict[str, int] = {}
    buying_eligible = 0
    for m in all_merchants:
        tier_dist[m.crawl_tier] = tier_dist.get(m.crawl_tier, 0) + 1
        trust_dist[m.trust_tier] = trust_dist.get(m.trust_tier, 0) + 1
        if meets_buying_threshold(m):
            buying_eligible += 1
    return {
        "total_active": len(all_merchants),
        "buying_eligible": buying_eligible,
        "crawl_tier_distribution": tier_dist,
        "trust_tier_distribution": trust_dist,
        "buying_quality_floor": BUYING_QUALITY_FLOOR,
        "buying_trust_tiers": sorted(BUYING_VIEW_TRUSTED_TIERS),
        "catalog_trust_tiers": sorted(CATALOG_VIEW_TIERS),
    }


@router.get("/watchlist", response_model=list[MerchantSummary])
def list_watchlist(
    db: Session = Depends(get_session),
) -> list[MerchantSummary]:
    """SC-52: Return merchants on the watch list."""
    merchants = db.scalars(
        select(Merchant)
        .where(Merchant.is_watched.is_(True), Merchant.is_active.is_(True))
        .order_by(Merchant.name)
    ).all()
    return [MerchantSummary.model_validate(m) for m in merchants]


@router.post("/{merchant_id}/watch", response_model=dict)
def add_to_watchlist(
    merchant_id: int,
    db: Session = Depends(get_session),
) -> dict:
    """SC-52: Add a merchant to the watch list."""
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    merchant.is_watched = True
    db.commit()
    return {"merchant_id": merchant_id, "is_watched": True}


@router.delete("/{merchant_id}/watch", response_model=dict)
def remove_from_watchlist(
    merchant_id: int,
    db: Session = Depends(get_session),
) -> dict:
    """SC-52: Remove a merchant from the watch list."""
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    merchant.is_watched = False
    db.commit()
    return {"merchant_id": merchant_id, "is_watched": False}


@router.get("/{merchant_id}/promos", response_model=list[MerchantPromoSchema])
def list_merchant_promos(
    merchant_id: int,
    db: Session = Depends(get_session),
    active_only: bool = Query(True),
) -> list[MerchantPromoSchema]:
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    q = select(MerchantPromo).where(MerchantPromo.merchant_id == merchant_id)
    if active_only:
        q = q.where(MerchantPromo.is_active.is_(True))
    q = q.order_by(MerchantPromo.estimated_value_cents.desc(), MerchantPromo.last_seen_at.desc())
    promos = db.scalars(q).all()
    return [MerchantPromoSchema.model_validate(p) for p in promos]
