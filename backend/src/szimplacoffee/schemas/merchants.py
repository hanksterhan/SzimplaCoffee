from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class ShippingPolicySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    free_shipping_threshold_cents: Optional[int]
    shipping_notes: str
    estimated_delivery_days: Optional[int]
    observed_at: datetime
    confidence: float

    @computed_field
    @property
    def free_shipping_threshold_dollars(self) -> Optional[float]:
        return self.free_shipping_threshold_cents / 100 if self.free_shipping_threshold_cents else None


class MerchantQualityProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    freshness_transparency_score: float
    shipping_clarity_score: float
    metadata_quality_score: float
    espresso_relevance_score: float
    service_confidence_score: float
    overall_quality_score: float
    last_reviewed_at: datetime


class MerchantPersonalProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    has_order_history: bool
    would_reorder: bool
    personal_trust_score: float
    average_rating: float
    notes: str
    last_ordered_at: Optional[datetime] = None


class MerchantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    canonical_domain: str
    homepage_url: str
    platform_type: str  # "shopify" | "woocommerce" | "agentic" | "unknown"
    country_code: str
    is_active: bool
    is_watched: bool = False  # SC-52 watch list
    crawl_tier: str  # "A" | "B" | "C"
    trust_tier: str  # "trusted" | "verified" | "candidate" | "rejected"
    created_at: datetime
    updated_at: datetime
    # SC-74: crawl health fields
    last_crawl_at: Optional[datetime] = None
    crawl_success: Optional[bool] = None
    product_count: int = 0
    metadata_pct: float = 0.0

    @computed_field
    @property
    def is_trusted(self) -> bool:
        return self.trust_tier in ("trusted", "verified")


class MerchantDetail(MerchantSummary):
    quality_profile: Optional[MerchantQualityProfileSchema] = None
    personal_profile: Optional[MerchantPersonalProfileSchema] = None
    shipping_policies: list[ShippingPolicySchema] = []
    # crawl_runs and products loaded separately via nested endpoints
