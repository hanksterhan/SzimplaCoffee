from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


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
    process_text: str  # mostly empty currently
    tasting_notes_text: str  # mostly empty currently
    product_category: str
    is_single_origin: bool
    is_espresso_recommended: bool
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime


class ProductDetail(ProductSummary):
    roast_cues: str
    variety_text: str
    variants: list[ProductVariantSchema] = []
