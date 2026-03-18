from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    merchant_count: int
    product_count: int
    variant_count: int
    offer_count: int
    promo_count: int
    crawl_run_count: int
    recommendation_count: int
    last_crawl_at: Optional[datetime]
    merchants_due_for_crawl: int = 0
    # Metadata fill-rate fields (SC-64)
    total_products: int = 0
    products_with_origin: int = 0
    products_with_process: int = 0
    products_with_roast_level: int = 0
