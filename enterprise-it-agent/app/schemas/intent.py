from typing import Literal

from pydantic import BaseModel, Field


IntentType = Literal[
    "knowledge_question",
    "ticket_query",
    "ticket_create",
    "asset_query",
    "smalltalk",
]


class IntentResult(BaseModel):
    intent: IntentType = Field(description="Predicted user intent")
    reason: str = Field(description="Short explanation for the prediction")
