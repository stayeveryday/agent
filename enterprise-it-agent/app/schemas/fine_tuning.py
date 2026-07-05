from typing import Any

from pydantic import BaseModel, Field


class FineTunedIntentPreviewRequest(BaseModel):
    question: str = Field(min_length=1, description="User question to classify")


class FineTunedIntentPreviewResponse(BaseModel):
    user_query: str
    provider: str
    adapter_dir: str
    raw_output: str
    cleaned_output: str
    extracted_json: dict[str, Any] | None
    normalized: dict[str, Any] | None
    validation_failures: list[str]
    route: str
    is_valid: bool
