from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.audit.log import list_audit_events
from app.demo.scenarios import get_demo_scenarios_doc
from app.evals.runner import run_evaluations
from app.graph.checkpoints import approve_checkpoint, create_checkpoint
from app.graph.workflow import run_minimal_graph
from app.observability.tracing import get_trace
from app.streaming.sse import stream_graph_run


REPORT_PATH = Path(__file__).resolve().parents[2] / "docs" / "acceptance_report.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pass(name: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "passed": True,
        "details": details or {},
        "failures": [],
    }


def _fail(name: str, failure: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "passed": False,
        "details": details or {},
        "failures": [failure],
    }


def _check_demo_doc() -> dict[str, Any]:
    doc = get_demo_scenarios_doc()
    content = doc["content"]
    if "# Demo Scenarios" not in content:
        return _fail("demo_doc", "Demo document title was not found.", {"path": doc["path"]})
    return _pass("demo_doc", {"path": doc["path"], "content_length": len(content)})


def _check_tool_eval() -> dict[str, Any]:
    result = run_evaluations(category="tool")
    if result["failed"]:
        return _fail("tool_eval", "Tool eval has failed cases.", result)
    return _pass("tool_eval", {"total": result["total"], "passed": result["passed"]})


def _check_memory_eval() -> dict[str, Any]:
    result = run_evaluations(category="memory")
    if result["failed"]:
        return _fail("memory_eval", "Memory eval has failed cases.", result)
    return _pass("memory_eval", {"total": result["total"], "passed": result["passed"]})


def _check_approval_eval() -> dict[str, Any]:
    result = run_evaluations(category="approval")
    if result["failed"]:
        return _fail("approval_eval", "Approval eval has failed cases.", result)
    return _pass("approval_eval", {"total": result["total"], "passed": result["passed"]})


def _check_trace_and_audit_eval() -> list[dict[str, Any]]:
    checks = []
    for category in ["trace", "audit"]:
        result = run_evaluations(category=category)
        if result["failed"]:
            checks.append(_fail(f"{category}_eval", f"{category} eval has failed cases.", result))
        else:
            checks.append(_pass(f"{category}_eval", {"total": result["total"], "passed": result["passed"]}))
    return checks


def _check_rag_eval() -> dict[str, Any]:
    result = run_evaluations(category="rag")
    if result["failed"]:
        return _fail("rag_eval", "RAG eval has failed cases.", result)
    return _pass("rag_eval", {"total": result["total"], "passed": result["passed"]})


def _check_approval_resume() -> dict[str, Any]:
    state = run_minimal_graph(
        user_query="Please create a high priority network ticket for u10077. Laptop cannot connect to office wifi.",
        session_id="acceptance-approval-001",
    )
    if state.get("approval_status") != "pending":
        return _fail("approval_resume", "Expected pending approval.", dict(state))

    checkpoint_id = create_checkpoint(state)
    approved = approve_checkpoint(checkpoint_id)
    tool_result = approved.get("tool_result", {})
    if approved.get("approval_status") != "approved" or not tool_result:
        return _fail("approval_resume", "Approval resume did not execute the tool.", dict(approved))

    return _pass(
        "approval_resume",
        {
            "approval_checkpoint_id": checkpoint_id,
            "approval_status": approved.get("approval_status"),
            "tool_name": approved.get("tool_name"),
            "has_tool_result": bool(tool_result),
        },
    )


def _check_trace_lookup() -> dict[str, Any]:
    state = run_minimal_graph(
        user_query="Please check ticket INC-1001 status.",
        session_id="acceptance-trace-001",
    )
    trace_id = state.get("trace_id")
    trace = get_trace(str(trace_id)) if trace_id else None
    if not trace or not trace.get("events"):
        return _fail("trace_lookup", "Trace not found or has no events.", {"trace_id": trace_id})
    return _pass(
        "trace_lookup",
        {
            "trace_id": trace_id,
            "event_count": len(trace.get("events", [])),
            "status": trace.get("status"),
        },
    )


def _check_audit_lookup() -> dict[str, Any]:
    events = list_audit_events(limit=20)
    if not events:
        return _fail("audit_lookup", "No audit events were found.")
    return _pass(
        "audit_lookup",
        {
            "event_count": len(events),
            "latest_event_type": events[0].get("event_type"),
            "latest_action": events[0].get("action"),
        },
    )


def _check_streaming() -> dict[str, Any]:
    body = "".join(
        stream_graph_run(
            user_query="Please check ticket INC-1001 status.",
            session_id="acceptance-stream-001",
        )
    )
    required_events = ["event: start", "event: state", "event: final", "event: done"]
    missing = [event for event in required_events if event not in body]
    if missing:
        return _fail("streaming", f"Missing SSE events: {missing}", {"body_preview": body[:300]})
    return _pass("streaming", {"events": required_events})


def _render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Acceptance Report",
        "",
        f"Generated at: `{result['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Total checks: `{result['total']}`",
        f"- Passed: `{result['passed']}`",
        f"- Failed: `{result['failed']}`",
        f"- Pass rate: `{result['pass_rate']:.2%}`",
        "",
        "## Checks",
        "",
    ]
    for check in result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"### {check['name']} - {status}")
        lines.append("")
        if check["details"]:
            lines.append("Details:")
            lines.append("")
            for key, value in check["details"].items():
                lines.append(f"- `{key}`: `{value}`")
            lines.append("")
        if check["failures"]:
            lines.append("Failures:")
            lines.append("")
            for failure in check["failures"]:
                lines.append(f"- {failure}")
            lines.append("")
    return "\n".join(lines)


def run_acceptance(include_slow: bool = False, write_report: bool = True) -> dict[str, Any]:
    checks = [
        _check_demo_doc(),
        _check_tool_eval(),
        _check_memory_eval(),
        _check_approval_eval(),
        *_check_trace_and_audit_eval(),
        _check_approval_resume(),
        _check_trace_lookup(),
        _check_audit_lookup(),
        _check_streaming(),
    ]
    if include_slow:
        checks.append(_check_rag_eval())

    total = len(checks)
    passed = sum(1 for check in checks if check["passed"])
    result = {
        "generated_at": _now_iso(),
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total) if total else 0,
        "checks": checks,
        "report_path": str(REPORT_PATH),
    }
    if write_report:
        REPORT_PATH.write_text(_render_report(result), encoding="utf-8")
    return result
