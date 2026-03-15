from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MerchantCandidateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_domain: str
    merchant_name: str
    homepage_url: str
    source_query: str
    platform_type: str
    confidence: float
    status: str  # "pending" | "approved" | "rejected"
    notes: str
    discovered_at: datetime
    reviewed_at: Optional[datetime]
