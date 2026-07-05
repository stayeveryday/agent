import json
from collections.abc import Iterator
from typing import Any

from app.graph.checkpoints import create_checkpoint
from app.graph.workflow import run_minimal_graph


def _sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _state_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace_id": state.get("trace_id"),
        "session_id": state.get("session_id"),
        "intent": state.get("intent"),
        "route_name": state.get("route_name"),
        "tool_name": state.get("tool_name"),
        "approval_status": state.get("approval_status"),
        "approval_checkpoint_id": state.get("approval_checkpoint_id"),
        "retrieved_docs_count": len(state.get("retrieved_docs", []) or []),
        "rag_sources": state.get("rag_sources", []),
        "has_tool_result": bool(state.get("tool_result")),
    }


def stream_graph_run(
    user_query: str,
    session_id: str | None = None,
    department: str = "general",
    access_level: str = "standard",
    approved: bool = False,
) -> Iterator[str]:
    yield _sse(
        "start",
        {
            "message": "Graph execution started.",
            "user_query": user_query,
            "session_id": session_id,
        },
    )

    try:
        state = run_minimal_graph(
            user_query=user_query,
            session_id=session_id,
            department=department,
            access_level=access_level,
            approved=approved,
        )
        if state.get("approval_status") == "pending":
            checkpoint_id = create_checkpoint(state)
            state["approval_checkpoint_id"] = checkpoint_id

        state_dict = dict(state)
        yield _sse("state", _state_summary(state_dict))
        yield _sse(
            "final",
            {
                "answer": state_dict.get("final_answer", ""),
                "state": _state_summary(state_dict),
            },
        )
        yield _sse("done", {"message": "Graph execution completed."})
    except Exception as exc:
        yield _sse("error", {"message": str(exc)})
