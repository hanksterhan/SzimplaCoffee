from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class CrawlRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    run_type: str
    adapter_name: str  # "shopify" | "woocommerce" | "agentic"
    started_at: datetime
    finished_at: Optional[datetime]
    status: str  # "started" | "completed" | "failed"
    confidence: float
    records_written: int
    error_summary: str
    # Crawl strategy layers (SC-51)
    catalog_strategy: str = "none"
    promo_strategy: str = "none"
    shipping_strategy: str = "none"
    metadata_strategy: str = "none"
    crawl_quality_score: float = 0.0

    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
