from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    chat_route_node,
    classify_intent_node,
    final_answer_node,
    rag_route_node,
    tool_route_node,
)
from app.graph.state import AgentState, build_initial_state
from app.memory.store import build_memory_context, resolve_user_query, update_session_from_state
from app.observability.tracing import finish_trace, record_event, start_trace, trace_node


def route_by_intent(state: AgentState) -> str:
    intent = state.get("intent")
    if intent == "knowledge_question":
        route = "rag"
    elif intent in {"ticket_query", "ticket_create", "asset_query"}:
        route = "tool"
    else:
        route = "chat"
    record_event(
        trace_id=state.get("trace_id"),
        name="route_by_intent",
        event_type="route",
        data={"intent": intent, "route": route},
    )
    return route


def build_minimal_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", trace_node("classify_intent", classify_intent_node))
    graph.add_node("rag_route", trace_node("rag_route", rag_route_node))
    graph.add_node("tool_route", trace_node("tool_route", tool_route_node))
    graph.add_node("chat_route", trace_node("chat_route", chat_route_node))
    graph.add_node("final_answer", trace_node("final_answer", final_answer_node))
    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "rag": "rag_route",
            "tool": "tool_route",
            "chat": "chat_route",
        },
    )
    graph.add_edge("rag_route", "final_answer")
    graph.add_edge("tool_route", "final_answer")
    graph.add_edge("chat_route", "final_answer")
    graph.add_edge("final_answer", END)
    return graph.compile()


def run_minimal_graph(
    user_query: str,
    department: str = "general",
    access_level: str = "standard",
    approved: bool = False,
    session_id: str | None = None,
) -> AgentState:
    app = build_minimal_graph()
    trace_id = start_trace(user_query=user_query, session_id=session_id)
    memory_context = build_memory_context(session_id)
    resolved_user_query = resolve_user_query(user_query=user_query, session_id=session_id)
    initial_state = build_initial_state(
        user_query=user_query,
        department=department,
        access_level=access_level,
        session_id=session_id,
        memory_context=memory_context,
        resolved_user_query=resolved_user_query,
    )
    initial_state["approved"] = approved
    initial_state["trace_id"] = trace_id
    try:
        state = app.invoke(initial_state)
    except Exception:
        finish_trace(trace_id=trace_id, status="failed", summary={"user_query": user_query})
        raise

    update_session_from_state(session_id, state)
    finish_trace(
        trace_id=trace_id,
        status="completed",
        summary={
            "intent": state.get("intent"),
            "route_name": state.get("route_name"),
            "tool_name": state.get("tool_name"),
            "approval_status": state.get("approval_status"),
            "has_final_answer": bool(state.get("final_answer")),
        },
    )
    return state


def describe_minimal_graph() -> dict[str, object]:
    return {
        "graph_name": "routed_agent_graph",
        "purpose": "LangGraph workflow with conditional routing by intent: input -> intent classification -> RAG/tool/chat route -> final answer.",
        "nodes": [
            {
                "name": "classify_intent",
                "description": "Runs the intent classifier and writes intent fields into state.",
            },
            {
                "name": "rag_route",
                "description": "Retrieves knowledge-base chunks and writes retrieved docs and sources into state.",
            },
            {
                "name": "tool_route",
                "description": "Builds tool arguments, checks approval for sensitive actions, executes allowed tools, and writes the result into state.",
            },
            {
                "name": "chat_route",
                "description": "Direct chat branch for smalltalk and simple conversational requests.",
            },
            {
                "name": "final_answer",
                "description": "Builds the user-facing answer. For the RAG route, it uses retrieved_docs as grounding context.",
            },
        ],
        "edges": [
            "START -> classify_intent",
            "classify_intent -> rag_route when intent is knowledge_question",
            "classify_intent -> tool_route when intent is ticket_query, ticket_create, or asset_query",
            "classify_intent -> chat_route when intent is smalltalk or unknown",
            "rag_route -> final_answer",
            "tool_route -> final_answer",
            "chat_route -> final_answer",
            "final_answer -> END",
        ],
    }
