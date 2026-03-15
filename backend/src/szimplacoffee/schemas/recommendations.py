import json
from datetime import datetime
from typing import Optional

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
