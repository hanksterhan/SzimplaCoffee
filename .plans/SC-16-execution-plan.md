# SC-16 Execution Plan: /api/v1/dashboard Endpoint

## Schema: `DashboardStats`

```python
# Add to schemas/__init__.py or new schemas/dashboard.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MerchantBreakdown(BaseModel):
    total: int
    active: int
    by_platform: dict[str, int]  # {"shopify": 14, "woocommerce": 1, "agentic": 1}
    by_trust_tier: dict[str, int]  # {"trusted": 2, "candidate": 14}
    trusted_count: int

class ProductStats(BaseModel):
    total: int
    active: int
    variants_total: int
    espresso_recommended: int
    single_origin: int

class OfferStats(BaseModel):
    total_snapshots: int
    avg_price_cents: int
    min_price_cents: int
    max_price_cents: int
    last_snapshot_at: Optional[datetime]

class CrawlStats(BaseModel):
    total_runs: int
    runs_last_7_days: int
    success_rate: float  # 0.0 - 1.0
    last_run_at: Optional[datetime]

class PromoStats(BaseModel):
    active_promos: int
    merchants_with_promos: int
    total_snapshots: int

class DashboardStats(BaseModel):
    merchants: MerchantBreakdown
    products: ProductStats
    offers: OfferStats
    crawls: CrawlStats
    promos: PromoStats
    generated_at: datetime
```

## Router: `backend/src/szimplacoffee/api/dashboard.py`

```python
from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    CrawlRun, Merchant, MerchantPromo, OfferSnapshot,
    Product, ProductVariant, PromoSnapshot,
)
from ..schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardStats:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    # Merchant stats
    total_merchants = db.query(func.count(Merchant.id)).scalar()
    active_merchants = db.query(func.count(Merchant.id)).filter(Merchant.is_active == True).scalar()
    platform_breakdown = dict(
        db.query(Merchant.platform_type, func.count(Merchant.id))
        .group_by(Merchant.platform_type)
        .all()
    )
    trust_breakdown = dict(
        db.query(Merchant.trust_tier, func.count(Merchant.id))
        .group_by(Merchant.trust_tier)
        .all()
    )
    trusted_count = (
        db.query(func.count(Merchant.id))
        .filter(Merchant.trust_tier.in_(["trusted", "verified"]))
        .scalar()
    )

    # Product stats
    total_products = db.query(func.count(Product.id)).scalar()
    active_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
    total_variants = db.query(func.count(ProductVariant.id)).scalar()
    espresso_recommended = (
        db.query(func.count(Product.id))
        .filter(Product.is_espresso_recommended == True)
        .scalar()
    )
    single_origin = (
        db.query(func.count(Product.id))
        .filter(Product.is_single_origin == True)
        .scalar()
    )

    # Offer stats
    offer_agg = db.query(
        func.count(OfferSnapshot.id),
        func.avg(OfferSnapshot.price_cents),
        func.min(OfferSnapshot.price_cents),
        func.max(OfferSnapshot.price_cents),
        func.max(OfferSnapshot.observed_at),
    ).one()

    # Crawl stats
    total_crawls = db.query(func.count(CrawlRun.id)).scalar()
    recent_crawls = (
        db.query(func.count(CrawlRun.id))
        .filter(CrawlRun.started_at >= week_ago)
        .scalar()
    )
    successful_crawls = (
        db.query(func.count(CrawlRun.id))
        .filter(CrawlRun.status == "completed")
        .scalar()
    )
    last_run_at = db.query(func.max(CrawlRun.started_at)).scalar()

    # Promo stats
    active_promos = (
        db.query(func.count(MerchantPromo.id))
        .filter(MerchantPromo.is_active == True)
        .scalar()
    )
    merchants_with_promos = (
        db.query(func.count(func.distinct(MerchantPromo.merchant_id)))
        .filter(MerchantPromo.is_active == True)
        .scalar()
    )
    total_promo_snapshots = db.query(func.count(PromoSnapshot.id)).scalar()

    return DashboardStats(
        merchants=MerchantBreakdown(
            total=total_merchants,
            active=active_merchants,
            by_platform=platform_breakdown,
            by_trust_tier=trust_breakdown,
            trusted_count=trusted_count,
        ),
        products=ProductStats(
            total=total_products,
            active=active_products,
            variants_total=total_variants,
            espresso_recommended=espresso_recommended,
            single_origin=single_origin,
        ),
        offers=OfferStats(
            total_snapshots=offer_agg[0] or 0,
            avg_price_cents=int(offer_agg[1] or 0),
            min_price_cents=offer_agg[2] or 0,
            max_price_cents=offer_agg[3] or 0,
            last_snapshot_at=offer_agg[4],
        ),
        crawls=CrawlStats(
            total_runs=total_crawls,
            runs_last_7_days=recent_crawls,
            success_rate=(successful_crawls / total_crawls) if total_crawls else 0.0,
            last_run_at=last_run_at,
        ),
        promos=PromoStats(
            active_promos=active_promos,
            merchants_with_promos=merchants_with_promos,
            total_snapshots=total_promo_snapshots,
        ),
        generated_at=now,
    )
```

## Expected Response (from DB)
```json
{
  "merchants": {"total": 16, "active": 16, "by_platform": {"shopify": 14, "woocommerce": 1, "agentic": 1}, "trusted_count": 2},
  "products": {"total": 910, "active": 910, "variants_total": 3207},
  "offers": {"total_snapshots": 9352, "avg_price_cents": 8000, "min_price_cents": 0, "max_price_cents": 173280},
  "crawls": {"total_runs": 55, "success_rate": 0.X},
  "promos": {"active_promos": 37, "merchants_with_promos": X}
}
```
