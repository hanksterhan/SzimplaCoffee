# SC-11 Execution Plan: Pydantic v2 Response Schemas

## Schemas to Create

### `schemas/common.py`
```python
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
```

### `schemas/merchants.py`
```python
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

class MerchantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    canonical_domain: str
    homepage_url: str
    platform_type: str  # "shopify" | "woocommerce" | "agentic" | "unknown"
    country_code: str
    is_active: bool
    crawl_tier: str  # "A" | "B" | "C"
    trust_tier: str  # "trusted" | "verified" | "candidate" | "rejected"
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_trusted(self) -> bool:
        return self.trust_tier in ("trusted", "verified")

class MerchantDetail(MerchantSummary):
    quality_profile: Optional[MerchantQualityProfileSchema] = None
    shipping_policies: list[ShippingPolicySchema] = []
    # crawl_runs and products loaded separately via nested endpoints
```

### `schemas/products.py`
```python
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
    name: str
    product_url: str
    image_url: str
    origin_text: str   # mostly empty currently
    process_text: str  # mostly empty currently
    tasting_notes_text: str  # mostly empty currently
    is_single_origin: bool
    is_espresso_recommended: bool
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime

class ProductDetail(ProductSummary):
    roast_cues: str
    variety_text: str
    variants: list[ProductVariantSchema] = []
```

### `schemas/crawls.py`
```python
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

    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
```

### `schemas/recommendations.py`
```python
import json
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, model_validator

class RecommendationRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_at: datetime
    request_json: str
    top_result_json: str
    alternatives_json: str
    wait_recommendation: bool
    model_version: str

    @model_validator(mode="after")
    def parse_json_fields(self) -> "RecommendationRunSchema":
        # Expose parsed versions as attributes
        object.__setattr__(self, "_request", json.loads(self.request_json or "{}"))
        object.__setattr__(self, "_top_result", json.loads(self.top_result_json or "{}"))
        return self
```

### `schemas/discovery.py`
```python
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
```

### `schemas/promos.py`
```python
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
```

## Test Strategy (`tests/test_schemas.py`)
- Instantiate each schema with `model_validate({...})` using test dict
- Verify computed fields work (price_dollars, is_trusted, etc.)
- Test `PaginatedResponse[MerchantSummary]` generic works
