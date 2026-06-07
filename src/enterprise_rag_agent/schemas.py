from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


IntentType = Literal["qa", "policy", "workflow", "tool", "chit_chat"]
ConfidenceLevel = Literal["low", "medium", "high"]


class RewriteResult(BaseModel):
    rewritten_query: str = Field(description="Rewrite query for search.")
    rationale: str = Field(description="Why the query was rewritten.")


class IntentResult(BaseModel):
    intent: IntentType
    needs_retrieval: bool
    needs_tools: bool
    tool_names: list[str] = Field(default_factory=list)
    reason: str


class ReflectionResult(BaseModel):
    confidence: ConfidenceLevel
    issues: list[str] = Field(default_factory=list)
    needs_follow_up: bool
    follow_up_question: str = ""


class MemoryRecord(BaseModel):
    session_id: str
    summary: str
    source_query: str
    final_answer: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict, total=False):
    session_id: str
    user_query: str
    recalled_memories: list[str]
    rewritten_query: str
    rewrite_reason: str
    intent: IntentType
    intent_reason: str
    needs_retrieval: bool
    needs_tools: bool
    requested_tools: list[str]
    retrieved_docs: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]
    answer_summary: str
    reflection: dict[str, Any]
    final_answer: str

