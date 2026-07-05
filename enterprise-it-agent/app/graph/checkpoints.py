from copy import deepcopy
from uuid import uuid4

from app.audit.log import record_audit_event
from app.graph.nodes import final_answer_node
from app.graph.state import AgentState
from app.memory.store import update_session_from_state
from app.tools.executor import run_tool


_CHECKPOINTS: dict[str, AgentState] = {}


def create_checkpoint(state: AgentState) -> str:
    checkpoint_id = str(uuid4())
    saved_state = deepcopy(state)
    saved_state["approval_checkpoint_id"] = checkpoint_id
    _CHECKPOINTS[checkpoint_id] = saved_state
    record_audit_event(
        event_type="checkpoint",
        action="create_approval_checkpoint",
        status="pending",
        trace_id=state.get("trace_id"),
        session_id=state.get("session_id"),
        approval_checkpoint_id=checkpoint_id,
        tool_name=state.get("tool_name"),
        tool_arguments=state.get("tool_arguments", {}),
        reason="Workflow paused for human approval.",
    )
    return checkpoint_id


def get_checkpoint(checkpoint_id: str) -> AgentState | None:
    state = _CHECKPOINTS.get(checkpoint_id)
    if state is None:
        return None
    return deepcopy(state)


def approve_checkpoint(checkpoint_id: str) -> AgentState:
    state = get_checkpoint(checkpoint_id)
    if state is None:
        raise ValueError(f"Checkpoint not found: {checkpoint_id}")
    if state.get("approval_status") != "pending":
        raise ValueError(f"Checkpoint is not pending approval: {checkpoint_id}")

    tool_name = state.get("tool_name")
    tool_arguments = state.get("tool_arguments", {})
    if not tool_name:
        raise ValueError(f"Checkpoint does not contain a tool call: {checkpoint_id}")

    state["approved"] = True
    state["approval_required"] = True
    state["approval_status"] = "approved"
    state["tool_result"] = run_tool(tool_name=tool_name, arguments=tool_arguments)
    record_audit_event(
        event_type="approval",
        action="approve_tool_call",
        status="approved",
        trace_id=state.get("trace_id"),
        session_id=state.get("session_id"),
        approval_checkpoint_id=checkpoint_id,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
        result=state["tool_result"],
    )
    state.pop("final_answer", None)
    state.update(final_answer_node(state))
    update_session_from_state(state.get("session_id"), state)
    _CHECKPOINTS[checkpoint_id] = deepcopy(state)
    return state


def reject_checkpoint(checkpoint_id: str, reason: str = "") -> AgentState:
    state = get_checkpoint(checkpoint_id)
    if state is None:
        raise ValueError(f"Checkpoint not found: {checkpoint_id}")
    if state.get("approval_status") != "pending":
        raise ValueError(f"Checkpoint is not pending approval: {checkpoint_id}")

    state["approved"] = False
    state["approval_required"] = True
    state["approval_status"] = "rejected"
    record_audit_event(
        event_type="approval",
        action="reject_tool_call",
        status="rejected",
        trace_id=state.get("trace_id"),
        session_id=state.get("session_id"),
        approval_checkpoint_id=checkpoint_id,
        tool_name=state.get("tool_name"),
        tool_arguments=state.get("tool_arguments", {}),
        reason=reason,
    )
    state["final_answer"] = (
        "The requested action was rejected and no tool was executed."
        if not reason
        else f"The requested action was rejected and no tool was executed. Reason: {reason}"
    )
    update_session_from_state(state.get("session_id"), state)
    _CHECKPOINTS[checkpoint_id] = deepcopy(state)
    return state
