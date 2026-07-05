from copy import deepcopy
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from app.graph.state import AgentState


_TRACES: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_trace(user_query: str, session_id: str | None = None) -> str:
    trace_id = str(uuid4())
    _TRACES[trace_id] = {
        "trace_id": trace_id,
        "session_id": session_id,
        "user_query": user_query,
        "started_at": _now_iso(),
        "finished_at": None,
        "status": "running",
        "events": [],
        "summary": {},
    }
    return trace_id


def record_event(
    trace_id: str | None,
    name: str,
    event_type: str,
    duration_ms: float | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    if not trace_id or trace_id not in _TRACES:
        return

    event = {
        "name": name,
        "type": event_type,
        "created_at": _now_iso(),
        "duration_ms": duration_ms,
        "data": data or {},
    }
    _TRACES[trace_id]["events"].append(event)


def finish_trace(trace_id: str | None, status: str, summary: dict[str, Any]) -> None:
    if not trace_id or trace_id not in _TRACES:
        return

    trace = _TRACES[trace_id]
    trace["status"] = status
    trace["finished_at"] = _now_iso()
    trace["summary"] = summary


def get_trace(trace_id: str) -> dict[str, Any] | None:
    trace = _TRACES.get(trace_id)
    if trace is None:
        return None
    return deepcopy(trace)


def list_traces(limit: int = 20) -> list[dict[str, Any]]:
    traces = list(_TRACES.values())[-limit:]
    return [
        {
            "trace_id": trace["trace_id"],
            "session_id": trace.get("session_id"),
            "user_query": trace.get("user_query"),
            "status": trace.get("status"),
            "started_at": trace.get("started_at"),
            "finished_at": trace.get("finished_at"),
            "event_count": len(trace.get("events", [])),
            "summary": trace.get("summary", {}),
        }
        for trace in reversed(traces)
    ]


def _compact_output(output: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in [
        "intent",
        "intent_reason",
        "route_name",
        "route_reason",
        "tool_name",
        "tool_arguments",
        "approval_required",
        "approval_status",
        "rag_sources",
        "error_message",
    ]:
        if key in output:
            compact[key] = output[key]

    if "retrieved_docs" in output:
        compact["retrieved_docs_count"] = len(output.get("retrieved_docs") or [])
    if "tool_result" in output:
        compact["has_tool_result"] = bool(output.get("tool_result"))
    if "final_answer" in output:
        compact["has_final_answer"] = bool(output.get("final_answer"))
    return compact


def trace_node(name: str, func: Callable[[AgentState], AgentState]) -> Callable[[AgentState], AgentState]:
    def wrapped(state: AgentState) -> AgentState:
        trace_id = state.get("trace_id")
        started = perf_counter()
        try:
            output = func(state)
        except Exception as exc:
            duration_ms = (perf_counter() - started) * 1000
            record_event(
                trace_id=trace_id,
                name=name,
                event_type="node_error",
                duration_ms=duration_ms,
                data={"error": str(exc)},
            )
            raise

        duration_ms = (perf_counter() - started) * 1000
        record_event(
            trace_id=trace_id,
            name=name,
            event_type="node",
            duration_ms=duration_ms,
            data=_compact_output(output),
        )
        return output

    return wrapped
