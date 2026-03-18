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
from ..services.scheduler import get_merchants_due_for_crawl

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
    merchants_due_for_crawl = len(get_merchants_due_for_crawl(db))

    # Metadata fill-rate counts (SC-64)
    # origin_country is nullable; process_family and roast_level default to "unknown"
    total_products = product_count  # reuse already-computed count
    products_with_origin = db.scalar(
        select(func.count(Product.id)).where(Product.origin_country.isnot(None))
    ) or 0
    products_with_process = db.scalar(
        select(func.count(Product.id)).where(
            (Product.process_family.isnot(None)) & (Product.process_family != "unknown")
        )
    ) or 0
    products_with_roast_level = db.scalar(
        select(func.count(Product.id)).where(
            (Product.roast_level.isnot(None)) & (Product.roast_level != "unknown")
        )
    ) or 0

    return DashboardMetrics(
        merchant_count=merchant_count,
        product_count=product_count,
        variant_count=variant_count,
        offer_count=offer_count,
        promo_count=promo_count,
        crawl_run_count=crawl_run_count,
        recommendation_count=recommendation_count,
        last_crawl_at=last_crawl_at,
        merchants_due_for_crawl=merchants_due_for_crawl,
        total_products=total_products,
        products_with_origin=products_with_origin,
        products_with_process=products_with_process,
        products_with_roast_level=products_with_roast_level,
    )
