import re

from app.audit.log import record_audit_event
from app.chains.basic_chat import ask
from app.fine_tuning.intent_provider import classify_with_configured_provider
from app.graph.state import AgentState
from app.rag.answer import collect_sources, generate_rag_answer
from app.rag.retriever import search_knowledge_base
from app.tools.executor import run_tool


def _none_if_general(value: str | None) -> str | None:
    if value in {None, "", "general"}:
        return None
    return value


def classify_intent_node(state: AgentState) -> AgentState:
    result = classify_with_configured_provider(state.get("resolved_user_query", state["user_query"]))
    return {
        "intent": result.intent,
        "intent_reason": result.reason,
        "intent_provider": result.provider,
        "intent_contract": {
            "ticket_id": result.ticket_id,
            "asset_tag": result.asset_tag,
            "priority": result.priority,
            "category": result.category,
            "raw_output": result.raw_output,
            "validation_failures": result.validation_failures,
        },
    }


def rag_route_node(state: AgentState) -> AgentState:
    retrieval = search_knowledge_base(
        query=state.get("resolved_user_query", state["user_query"]),
        top_k=4,
        fetch_k=8,
        department=_none_if_general(state.get("department")),
        access_level=_none_if_general(state.get("access_level")),
    )
    results = retrieval["results"]
    return {
        "route_name": "rag",
        "route_reason": "Knowledge questions should use retrieved knowledge base context.",
        "retrieved_docs": results,
        "rag_sources": collect_sources(results),
    }


def _find_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(0)


def _build_tool_call(state: AgentState) -> tuple[str, dict[str, object]]:
    query = state.get("resolved_user_query", state["user_query"])
    intent = state.get("intent")

    if intent == "ticket_query":
        ticket_id = _find_first(r"\b(?:INC|REQ)-\d+\b", query)
        return "get_ticket_status", {"ticket_id": ticket_id or query}

    if intent == "asset_query":
        employee_id = _find_first(r"\bu\d+\b", query)
        asset_tag = _find_first(r"\b(?:LT|DT)-\d{4}-\d+\b", query)
        hostname = _find_first(r"\b[A-Z]{2}-[A-Z]+-\d+\b", query)
        arguments = {
            key: value
            for key, value in {
                "employee_id": employee_id,
                "asset_tag": asset_tag,
                "hostname": hostname,
            }.items()
            if value
        }
        return "lookup_asset", arguments

    requester = _find_first(r"\bu\d+\b", query) or "unknown"
    lowered = query.lower()
    category = "other"
    if "email" in lowered or "outlook" in lowered:
        category = "email"
    elif "vpn" in lowered or "network" in lowered or "wifi" in lowered:
        category = "network"
    elif "laptop" in lowered or "monitor" in lowered or "hardware" in lowered:
        category = "hardware"
    elif "account" in lowered or "password" in lowered:
        category = "account"

    priority = "medium"
    if "urgent" in lowered or "high" in lowered or "cannot work" in lowered:
        priority = "high"
    elif "low" in lowered:
        priority = "low"

    return "create_ticket", {
        "requester": requester,
        "summary": query,
        "category": category,
        "priority": priority,
    }


def tool_route_node(state: AgentState) -> AgentState:
    tool_name, tool_arguments = _build_tool_call(state)
    if tool_name == "create_ticket" and not state.get("approved", False):
        record_audit_event(
            event_type="approval_required",
            action="prepare_tool_call",
            status="pending",
            trace_id=state.get("trace_id"),
            session_id=state.get("session_id"),
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            reason="Sensitive tool call requires approval.",
        )
        return {
            "route_name": "tool",
            "route_reason": "Ticket creation is a sensitive action and needs human approval before execution.",
            "tool_name": tool_name,
            "tool_arguments": tool_arguments,
            "approval_required": True,
            "approval_status": "pending",
        }

    tool_result = run_tool(tool_name=tool_name, arguments=tool_arguments)
    record_audit_event(
        event_type="tool_call",
        action="execute_tool",
        status="success",
        trace_id=state.get("trace_id"),
        session_id=state.get("session_id"),
        tool_name=tool_name,
        tool_arguments=tool_arguments,
        result=tool_result,
    )
    return {
        "route_name": "tool",
        "route_reason": "Ticket and asset requests should use business tools.",
        "tool_name": tool_name,
        "tool_arguments": tool_arguments,
        "tool_result": tool_result,
        "approval_required": tool_name == "create_ticket",
        "approval_status": "approved" if tool_name == "create_ticket" else "not_required",
    }


def chat_route_node(state: AgentState) -> AgentState:
    return {
        "route_name": "chat",
        "route_reason": "Smalltalk can be answered directly without retrieval or tools.",
    }


def final_answer_node(state: AgentState) -> AgentState:
    if state.get("final_answer"):
        return {}

    if state.get("route_name") == "rag":
        answer = generate_rag_answer(
            question=state.get("resolved_user_query", state["user_query"]),
            results=state.get("retrieved_docs", []),
        )
        return {
            "final_answer": answer,
        }

    if state.get("route_name") == "tool":
        if state.get("approval_status") == "pending":
            return {
                "final_answer": (
                    "This request is ready to create a ticket, but it needs human approval before execution. "
                    f"Planned tool: {state.get('tool_name')}. "
                    f"Planned arguments: {state.get('tool_arguments', {})}."
                )
            }

        answer = ask(
            question=(
                f"User question: {state['user_query']}\n"
                f"Resolved question: {state.get('resolved_user_query', state['user_query'])}\n"
                f"Memory context: {state.get('memory_context', '')}\n"
                f"Detected intent: {state.get('intent', 'unknown')}\n"
                f"Selected tool: {state.get('tool_name', 'unknown')}\n"
                f"Tool arguments: {state.get('tool_arguments', {})}\n"
                f"Tool result: {state.get('tool_result', {})}\n\n"
                "Answer the user based on the tool result. Be concise and actionable."
            ),
            style="guided",
        )
        return {
            "final_answer": answer,
        }

    answer = ask(
        question=(
            f"User question: {state['user_query']}\n"
            f"Resolved question: {state.get('resolved_user_query', state['user_query'])}\n"
            f"Memory context: {state.get('memory_context', '')}\n"
             f"Detected intent: {state.get('intent', 'unknown')}\n"
            f"Intent reason: {state.get('intent_reason', '')}\n\n"
            f"Selected route: {state.get('route_name', 'unknown')}\n"
            f"Route reason: {state.get('route_reason', '')}\n\n"
            "Give a helpful response to the user."
        ),
        style="guided",
    )
    return {
        "final_answer": answer,
    }


def error_node(state: AgentState) -> AgentState:
    return {
        "final_answer": "The workflow failed before a final answer could be generated.",
        "error_message": state.get("error_message", "Unknown workflow error."),
    }
