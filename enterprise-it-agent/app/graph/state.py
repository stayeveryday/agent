from typing import Literal, TypedDict

from app.schemas.intent import IntentType


ApprovalStatus = Literal["not_required", "pending", "approved", "rejected"]


class AgentState(TypedDict, total=False):
    trace_id: str
    session_id: str
    user_query: str
    resolved_user_query: str
    memory_context: str
    intent: IntentType
    intent_reason: str
    intent_provider: str
    intent_contract: dict[str, object]
    route_name: str
    route_reason: str
    retrieved_docs: list[dict[str, object]]
    rag_sources: list[str]
    tool_name: str
    tool_arguments: dict[str, object]
    tool_result: dict[str, object]
    final_answer: str
    approval_checkpoint_id: str
    department: str
    access_level: str
    approved: bool
    approval_required: bool
    approval_status: ApprovalStatus
    error_message: str


def build_initial_state(
    user_query: str,
    department: str = "general",
    access_level: str = "standard",
    session_id: str | None = None,
    memory_context: str = "",
    resolved_user_query: str | None = None,
) -> AgentState:
    state: AgentState = {
        "user_query": user_query,
        "resolved_user_query": resolved_user_query or user_query,
        "memory_context": memory_context,
        "retrieved_docs": [],
        "tool_arguments": {},
        "department": department,
        "access_level": access_level,
        "approved": False,
        "approval_required": False,
        "approval_status": "not_required",
        "error_message": "",
    }
    if session_id:
        state["session_id"] = session_id
    return state


def describe_agent_state() -> dict[str, object]:
    return {
        "state_name": "AgentState",
        "purpose": "Shared state passed between LangGraph nodes in the enterprise agent workflow.",
        "fields": [
            {
                "name": "trace_id",
                "type": "str",
                "required_at_start": False,
                "description": "Trace identifier used to inspect graph execution events.",
            },
            {
                "name": "session_id",
                "type": "str",
                "required_at_start": False,
                "description": "Conversation session identifier used to load and update session memory.",
            },
            {
                "name": "user_query",
                "type": "str",
                "required_at_start": True,
                "description": "Original user request.",
            },
            {
                "name": "resolved_user_query",
                "type": "str",
                "required_at_start": True,
                "description": "User request enriched with session memory when needed.",
            },
            {
                "name": "memory_context",
                "type": "str",
                "required_at_start": False,
                "description": "Short session memory summary injected into the graph.",
            },
            {
                "name": "intent",
                "type": "IntentType",
                "required_at_start": False,
                "description": "Intent predicted by the classifier node.",
            },
            {
                "name": "intent_reason",
                "type": "str",
                "required_at_start": False,
                "description": "Why the classifier chose that intent.",
            },
            {
                "name": "route_name",
                "type": "str",
                "required_at_start": False,
                "description": "Workflow branch selected after intent classification.",
            },
            {
                "name": "route_reason",
                "type": "str",
                "required_at_start": False,
                "description": "Short explanation for why the workflow selected that branch.",
            },
            {
                "name": "retrieved_docs",
                "type": "list[dict[str, object]]",
                "required_at_start": True,
                "description": "Documents returned by the RAG retrieval step.",
            },
            {
                "name": "rag_sources",
                "type": "list[str]",
                "required_at_start": False,
                "description": "Unique source files used by the RAG answer step.",
            },
            {
                "name": "tool_name",
                "type": "str",
                "required_at_start": False,
                "description": "Tool selected for execution.",
            },
            {
                "name": "tool_arguments",
                "type": "dict[str, object]",
                "required_at_start": True,
                "description": "Structured arguments for the selected tool.",
            },
            {
                "name": "tool_result",
                "type": "dict[str, object]",
                "required_at_start": False,
                "description": "Result returned by tool execution.",
            },
            {
                "name": "final_answer",
                "type": "str",
                "required_at_start": False,
                "description": "Answer returned to the user at the end of the graph.",
            },
            {
                "name": "approval_checkpoint_id",
                "type": "str",
                "required_at_start": False,
                "description": "Identifier used to resume a pending approval workflow.",
            },
            {
                "name": "department",
                "type": "str",
                "required_at_start": True,
                "description": "Department or business scope for retrieval and authorization.",
            },
            {
                "name": "access_level",
                "type": "str",
                "required_at_start": True,
                "description": "Access boundary such as standard or restricted.",
            },
            {
                "name": "approval_required",
                "type": "bool",
                "required_at_start": True,
                "description": "Whether the current action needs human approval.",
            },
            {
                "name": "approved",
                "type": "bool",
                "required_at_start": True,
                "description": "Whether the human has approved a sensitive action.",
            },
            {
                "name": "approval_status",
                "type": "ApprovalStatus",
                "required_at_start": True,
                "description": "Approval lifecycle state for sensitive actions.",
            },
            {
                "name": "error_message",
                "type": "str",
                "required_at_start": True,
                "description": "Captured error message when a node fails.",
            },
        ],
    }
