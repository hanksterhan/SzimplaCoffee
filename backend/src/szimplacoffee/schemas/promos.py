from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class MerchantPromoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: int
    promo_key: str
    promo_type: str
    title: str
    details: str
    code: Optional[str]
    estimated_value_cents: Optional[int]
    confidence: float
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime

    @computed_field
    @property
    def estimated_value_dollars(self) -> Optional[float]:
        return self.estimated_value_cents / 100 if self.estimated_value_cents else None
