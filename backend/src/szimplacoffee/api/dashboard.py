from __future__ import annotations


from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import (
    CrawlRun,
    Merchant,
    MerchantPromo,
    OfferSnapshot,
    Product,
    ProductVariant,
    RecommendationRun,
)
from ..schemas.dashboard import DashboardMetrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_session)) -> DashboardMetrics:
    merchant_count = db.scalar(func.count(Merchant.id)) or 0
    product_count = db.scalar(func.count(Product.id)) or 0
    variant_count = db.scalar(func.count(ProductVariant.id)) or 0
    offer_count = db.scalar(func.count(OfferSnapshot.id)) or 0
    promo_count = db.scalar(
        select(func.count(MerchantPromo.id)).where(MerchantPromo.is_active.is_(True))
    ) or 0
    crawl_run_count = db.scalar(func.count(CrawlRun.id)) or 0
    recommendation_count = db.scalar(func.count(RecommendationRun.id)) or 0
    last_crawl_at = db.scalar(select(func.max(CrawlRun.started_at)))

    return DashboardMetrics(
        merchant_count=merchant_count,
        product_count=product_count,
        variant_count=variant_count,
        offer_count=offer_count,
        promo_count=promo_count,
        crawl_run_count=crawl_run_count,
        recommendation_count=recommendation_count,
        last_crawl_at=last_crawl_at,
    )
