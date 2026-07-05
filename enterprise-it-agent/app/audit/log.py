from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


_AUDIT_EVENTS: list[dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_audit_event(
    event_type: str,
    action: str,
    status: str,
    trace_id: str | None = None,
    session_id: str | None = None,
    approval_checkpoint_id: str | None = None,
    tool_name: str | None = None,
    tool_arguments: dict[str, object] | None = None,
    result: dict[str, object] | None = None,
    reason: str = "",
) -> dict[str, Any]:
    event = {
        "audit_id": str(uuid4()),
        "event_type": event_type,
        "action": action,
        "status": status,
        "trace_id": trace_id,
        "session_id": session_id,
        "approval_checkpoint_id": approval_checkpoint_id,
        "tool_name": tool_name,
        "tool_arguments": tool_arguments or {},
        "result": result or {},
        "reason": reason,
        "created_at": _now_iso(),
    }
    _AUDIT_EVENTS.append(event)
    return deepcopy(event)


def list_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    return deepcopy(list(reversed(_AUDIT_EVENTS[-limit:])))


def get_audit_event(audit_id: str) -> dict[str, Any] | None:
    for event in _AUDIT_EVENTS:
        if event["audit_id"] == audit_id:
            return deepcopy(event)
    return None
