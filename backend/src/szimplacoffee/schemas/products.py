from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


RoastLevel = Literal["light", "light-medium", "medium", "medium-dark", "dark", "unknown"]
ProcessFamily = Literal["washed", "natural", "honey", "anaerobic", "wet-hulled", "blend", "unknown"]
MetadataSource = Literal["unknown", "structured", "parser", "agentic", "override"]


class OfferSnapshotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    observed_at: datetime
    price_cents: int
    compare_at_price_cents: Optional[int]
    subscription_price_cents: Optional[int]
    is_on_sale: bool
    is_available: bool
    source_url: str

    @computed_field
    @property
    def price_dollars(self) -> float:
        return self.price_cents / 100


class ProductVariantSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_variant_id: str
    label: str
    weight_grams: Optional[int]  # 340 (12oz) or 2268 (5lb) most common
    is_whole_bean: bool
    is_available: bool
    latest_offer: Optional[OfferSnapshotSchema] = None
    offers: list[OfferSnapshotSchema] = []


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    merchant_name: str = ""
    name: str
    product_url: str
    image_url: str
    origin_text: str   # mostly empty currently
    origin_country: Optional[str] = None
    origin_region: Optional[str] = None
    process_text: str  # mostly empty currently
    process_family: ProcessFamily = "unknown"
    tasting_notes_text: str  # mostly empty currently
    roast_level: RoastLevel = "unknown"
    metadata_confidence: float = 0.0
    metadata_source: MetadataSource = "unknown"
    product_category: str
    is_single_origin: bool
    is_espresso_recommended: bool
    is_active: bool
    latest_price_cents: Optional[int] = None
    latest_compare_at_price_cents: Optional[int] = None
    latest_discount_percent: Optional[int] = None
    primary_weight_grams: Optional[int] = None
    primary_is_whole_bean: bool = False
    first_seen_at: datetime
    last_seen_at: datetime


class ProductDetail(ProductSummary):
    roast_cues: str
    variety_text: str
    variants: list[ProductVariantSchema] = []
