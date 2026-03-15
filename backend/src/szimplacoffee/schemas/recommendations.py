import ast
import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


def _safe_parse(value: str, default):
    """Parse a JSON or Python repr string safely."""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        try:
            return ast.literal_eval(value)
        except Exception:
            return default


class RecommendationRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_at: datetime
    request_json: str
    top_result_json: str
    alternatives_json: str
    wait_recommendation: bool
    model_version: str
