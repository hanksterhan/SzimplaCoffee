from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PurchaseHistorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    product_variant_id: Optional[int]
    purchased_at: datetime
    price_cents: int
    quantity: int
    notes: Optional[str]
    rating: Optional[int]
    created_at: datetime


class BrewFeedbackSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_history_id: Optional[int]
    product_variant_id: Optional[int]
    brewed_at: datetime
    brew_method: Optional[str]
    dose_grams: Optional[float]
    yield_grams: Optional[float]
    brew_time_seconds: Optional[int]
    grind_setting: Optional[str]
    tasting_notes: Optional[str]
    overall_score: Optional[int]
    would_buy_again: Optional[bool]
    created_at: datetime
