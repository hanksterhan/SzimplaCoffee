from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── BrewFeedback ────────────────────────────────────────────────────────────

class BrewFeedbackCreate(BaseModel):
    shot_style: str
    grinder: str = "Timemore Sculptor 078S"
    basket: str = ""
    rating: float
    would_rebuy: bool = True
    difficulty_score: float = 3.0
    notes: str = ""


class BrewFeedbackUpdate(BaseModel):
    shot_style: Optional[str] = None
    grinder: Optional[str] = None
    basket: Optional[str] = None
    rating: Optional[float] = None
    would_rebuy: Optional[bool] = None
    difficulty_score: Optional[float] = None
    notes: Optional[str] = None


class BrewFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_id: int
    shot_style: str
    grinder: str
    basket: str
    rating: float
    would_rebuy: bool
    difficulty_score: float
    notes: str


# ── PurchaseHistory ──────────────────────────────────────────────────────────

class PurchaseCreate(BaseModel):
    merchant_id: int
    product_name: str
    origin_text: str = ""
    process_text: str = ""
    price_cents: int
    weight_grams: int
    purchased_at: Optional[datetime] = None
    source_system: str = "manual"
    source_ref: str = ""
    recommendation_run_id: Optional[int] = None


class PurchaseUpdate(BaseModel):
    merchant_id: Optional[int] = None
    product_name: Optional[str] = None
    origin_text: Optional[str] = None
    process_text: Optional[str] = None
    price_cents: Optional[int] = None
    weight_grams: Optional[int] = None
    purchased_at: Optional[datetime] = None
    source_system: Optional[str] = None
    source_ref: Optional[str] = None
    recommendation_run_id: Optional[int] = None


class PurchaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    product_name: str
    origin_text: str
    process_text: str
    price_cents: int
    weight_grams: int
    purchased_at: datetime
    source_system: str
    source_ref: str
    feedback_count: int = 0
    recommendation_run_id: Optional[int] = None


class PurchaseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    product_name: str
    origin_text: str
    process_text: str
    price_cents: int
    weight_grams: int
    purchased_at: datetime
    source_system: str
    source_ref: str
    recommendation_run_id: Optional[int] = None
    brew_feedback: list[BrewFeedbackOut] = []


# ── Stats ────────────────────────────────────────────────────────────────────

class PurchaseStats(BaseModel):
    total_purchases: int
    total_spent_cents: int
    avg_price_per_lb_cents: float
    favorite_merchant_id: Optional[int]
    favorite_merchant_name: Optional[str]


# ── Buying Pattern Intelligence ──────────────────────────────────────────────

class TopRoaster(BaseModel):
    merchant_name: str
    count: int


class BuyingPatternStats(BaseModel):
    """Behavioural buying intelligence derived from purchase history."""

    days_since_last_order: Optional[int]
    top_roasters: list[TopRoaster]
    avg_grams_per_week: Optional[float]


# ── Backward-compat aliases (used by schemas/__init__.py) ─────────────────────
PurchaseHistorySchema = PurchaseSummary
BrewFeedbackSchema = BrewFeedbackOut
