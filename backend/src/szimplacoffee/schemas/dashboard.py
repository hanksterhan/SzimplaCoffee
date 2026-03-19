from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MetadataFillRates(BaseModel):
    origin_pct: int
    process_pct: int
    roast_pct: int
    variety_pct: int


class GoalStatus(BaseModel):
    """Boolean completion flags mirroring autopilot/goal.yaml success_criteria."""

    merchants_15_plus: bool
    metadata_70pct: bool
    recs_produce_results: bool
    today_works: bool
    purchases_10_plus: bool
    brew_feedback_3_plus: bool
    ui_works: bool
    tests_pass: bool
    all_complete: bool


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
    # SC-88: structured fill-rate percentages
    metadata_fill_rates: MetadataFillRates = MetadataFillRates(
        origin_pct=0, process_pct=0, roast_pct=0, variety_pct=0
    )
    # SC-90: goal completion status
    goal_status: GoalStatus = GoalStatus(
        merchants_15_plus=False,
        metadata_70pct=False,
        recs_produce_results=False,
        today_works=False,
        purchases_10_plus=False,
        brew_feedback_3_plus=False,
        ui_works=True,
        tests_pass=True,
        all_complete=False,
    )
