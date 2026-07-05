import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.graph.state import AgentState


_SESSIONS: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_session_memory(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.setdefault(
        session_id,
        {
            "session_id": session_id,
            "messages": [],
            "last_intent": None,
            "last_ticket_id": None,
            "last_asset_id": None,
            "last_tool_name": None,
            "updated_at": _now_iso(),
        },
    )
    return deepcopy(session)


def build_memory_context(session_id: str | None) -> str:
    if not session_id:
        return ""

    session = get_session_memory(session_id)
    parts = []
    if session.get("last_intent"):
        parts.append(f"last_intent={session['last_intent']}")
    if session.get("last_ticket_id"):
        parts.append(f"last_ticket_id={session['last_ticket_id']}")
    if session.get("last_asset_id"):
        parts.append(f"last_asset_id={session['last_asset_id']}")
    if session.get("last_tool_name"):
        parts.append(f"last_tool_name={session['last_tool_name']}")

    recent_messages = session.get("messages", [])[-4:]
    if recent_messages:
        summary = " | ".join(
            f"{item.get('role')}: {item.get('content')}" for item in recent_messages
        )
        parts.append(f"recent_messages={summary}")

    return "\n".join(parts)


def resolve_user_query(user_query: str, session_id: str | None) -> str:
    if not session_id:
        return user_query

    session = get_session_memory(session_id)
    last_ticket_id = session.get("last_ticket_id")
    if last_ticket_id and not re.search(r"\b(?:INC|REQ)-\d+\b", user_query, re.IGNORECASE):
        lowered = user_query.lower()
        if any(token in lowered for token in ["it", "status", "progress"]) or any(
            token in user_query for token in ["它", "这个", "状态", "进度", "怎么样"]
        ):
            return f"{user_query}\nPrevious ticket id from session memory: {last_ticket_id}"

    return user_query


def update_session_from_state(session_id: str | None, state: AgentState) -> None:
    if not session_id:
        return

    session = get_session_memory(session_id)
    messages = session.setdefault("messages", [])
    messages.append(
        {
            "role": "user",
            "content": state.get("user_query", ""),
            "created_at": _now_iso(),
        }
    )
    if state.get("final_answer"):
        messages.append(
            {
                "role": "assistant",
                "content": state.get("final_answer", ""),
                "created_at": _now_iso(),
            }
        )

    if state.get("intent"):
        session["last_intent"] = state["intent"]
    if state.get("tool_name"):
        session["last_tool_name"] = state["tool_name"]

    tool_arguments = state.get("tool_arguments", {})
    if isinstance(tool_arguments, dict):
        if tool_arguments.get("ticket_id"):
            session["last_ticket_id"] = tool_arguments["ticket_id"]
        if tool_arguments.get("asset_tag"):
            session["last_asset_id"] = tool_arguments["asset_tag"]
        elif tool_arguments.get("hostname"):
            session["last_asset_id"] = tool_arguments["hostname"]
        elif tool_arguments.get("employee_id"):
            session["last_asset_id"] = tool_arguments["employee_id"]

    tool_result = state.get("tool_result", {})
    if isinstance(tool_result, dict):
        result = tool_result.get("result", {})
        if isinstance(result, dict):
            ticket = result.get("ticket")
            if isinstance(ticket, dict) and ticket.get("ticket_id"):
                session["last_ticket_id"] = ticket["ticket_id"]

    session["messages"] = messages[-20:]
    session["updated_at"] = _now_iso()
    _SESSIONS[session_id] = session


def clear_session_memory(session_id: str) -> bool:
    return _SESSIONS.pop(session_id, None) is not None
