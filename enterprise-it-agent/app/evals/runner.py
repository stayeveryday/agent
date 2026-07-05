from collections import defaultdict
from typing import Any

from app.audit.log import list_audit_events
from app.evals.dataset import load_eval_dataset
from app.graph.checkpoints import create_checkpoint
from app.graph.workflow import run_minimal_graph
from app.memory.store import clear_session_memory
from app.observability.tracing import get_trace


def _expected_input(case_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_query": str(case_input["user_query"]),
        "session_id": case_input.get("session_id"),
        "department": case_input.get("department", "general"),
        "access_level": case_input.get("access_level", "standard"),
        "approved": bool(case_input.get("approved", False)),
    }


def _run_graph_case(case_input: dict[str, Any]) -> dict[str, Any]:
    params = _expected_input(case_input)
    state = run_minimal_graph(**params)
    if state.get("approval_status") == "pending":
        checkpoint_id = create_checkpoint(state)
        state["approval_checkpoint_id"] = checkpoint_id
    return dict(state)


def _check_equal(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
    key: str,
) -> None:
    if key in expected and actual.get(key) != expected[key]:
        failures.append(f"{key}: expected {expected[key]!r}, got {actual.get(key)!r}")


def _check_bool(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
    key: str,
    actual_key: str,
) -> None:
    if key in expected and bool(actual.get(actual_key)) is not bool(expected[key]):
        failures.append(
            f"{actual_key}: expected truthy={bool(expected[key])}, got {bool(actual.get(actual_key))}"
        )


def _check_tool_arguments(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    required = expected.get("tool_arguments_contains")
    if not isinstance(required, dict):
        return

    arguments = actual.get("tool_arguments", {})
    if not isinstance(arguments, dict):
        failures.append("tool_arguments: expected dict, got non-dict")
        return

    for key, value in required.items():
        if arguments.get(key) != value:
            failures.append(
                f"tool_arguments.{key}: expected {value!r}, got {arguments.get(key)!r}"
            )


def _check_rag(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    if "min_retrieved_docs" in expected:
        docs = actual.get("retrieved_docs", [])
        if not isinstance(docs, list) or len(docs) < int(expected["min_retrieved_docs"]):
            failures.append(
                f"retrieved_docs: expected at least {expected['min_retrieved_docs']}, got {len(docs) if isinstance(docs, list) else 'non-list'}"
            )

    required_source = expected.get("required_source_contains")
    if required_source:
        sources = actual.get("rag_sources", [])
        if not any(str(required_source) in str(source) for source in sources):
            failures.append(f"rag_sources: expected source containing {required_source!r}")


def _check_trace(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    if expected.get("has_trace_id") is True and not actual.get("trace_id"):
        failures.append("trace_id: expected trace_id to exist")

    if actual.get("trace_id"):
        trace = get_trace(str(actual["trace_id"]))
        if trace is None:
            failures.append("trace: trace_id was returned but trace was not found")
        elif not trace.get("events"):
            failures.append("trace: expected at least one trace event")


def _check_audit(
    failures: list[str],
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    event_type = expected.get("audit_event_type")
    if not event_type:
        return

    trace_id = actual.get("trace_id")
    session_id = actual.get("session_id")
    events = list_audit_events(limit=200)
    matched = [
        event
        for event in events
        if event.get("event_type") == event_type
        and (
            (trace_id and event.get("trace_id") == trace_id)
            or (session_id and event.get("session_id") == session_id)
        )
    ]
    if not matched:
        failures.append(f"audit: expected event_type {event_type!r}")


def evaluate_state(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ["intent", "route_name", "tool_name", "approval_status"]:
        _check_equal(failures, actual, expected, key)

    _check_bool(failures, actual, expected, "has_tool_result", "tool_result")
    _check_bool(failures, actual, expected, "has_final_answer", "final_answer")
    _check_bool(failures, actual, expected, "requires_checkpoint", "approval_checkpoint_id")

    resolved_query_contains = expected.get("resolved_query_contains")
    if resolved_query_contains and resolved_query_contains not in str(actual.get("resolved_user_query", "")):
        failures.append(
            f"resolved_user_query: expected to contain {resolved_query_contains!r}"
        )

    _check_tool_arguments(failures, actual, expected)
    _check_rag(failures, actual, expected)
    _check_trace(failures, actual, expected)
    _check_audit(failures, actual, expected)
    return failures


def _clear_case_sessions(case: dict[str, Any]) -> None:
    inputs = []
    if isinstance(case.get("input"), dict):
        inputs.append(case["input"])
    for step in case.get("steps", []):
        if isinstance(step.get("input"), dict):
            inputs.append(step["input"])

    for item in inputs:
        session_id = item.get("session_id")
        if session_id:
            clear_session_memory(str(session_id))


def _evaluate_single_step_case(case: dict[str, Any]) -> dict[str, Any]:
    state = _run_graph_case(case["input"])
    failures = evaluate_state(state, case.get("expected", {}))
    return {
        "id": case.get("id"),
        "category": case.get("category"),
        "passed": not failures,
        "failures": failures,
        "actual": {
            "intent": state.get("intent"),
            "route_name": state.get("route_name"),
            "tool_name": state.get("tool_name"),
            "tool_arguments": state.get("tool_arguments"),
            "approval_status": state.get("approval_status"),
            "retrieved_docs_count": len(state.get("retrieved_docs", []) or []),
            "rag_sources": state.get("rag_sources", []),
            "has_tool_result": bool(state.get("tool_result")),
            "has_final_answer": bool(state.get("final_answer")),
            "has_trace_id": bool(state.get("trace_id")),
            "has_checkpoint": bool(state.get("approval_checkpoint_id")),
            "resolved_user_query": state.get("resolved_user_query"),
        },
    }


def _evaluate_multi_step_case(case: dict[str, Any]) -> dict[str, Any]:
    step_results = []
    failures = []
    for index, step in enumerate(case.get("steps", []), start=1):
        state = _run_graph_case(step["input"])
        step_failures = evaluate_state(state, step.get("expected", {}))
        if step_failures:
            failures.extend(f"step {index}: {failure}" for failure in step_failures)
        step_results.append(
            {
                "step": index,
                "passed": not step_failures,
                "failures": step_failures,
                "actual": {
                    "intent": state.get("intent"),
                    "route_name": state.get("route_name"),
                    "tool_name": state.get("tool_name"),
                    "tool_arguments": state.get("tool_arguments"),
                    "resolved_user_query": state.get("resolved_user_query"),
                },
            }
        )

    return {
        "id": case.get("id"),
        "category": case.get("category"),
        "passed": not failures,
        "failures": failures,
        "steps": step_results,
    }


def run_evaluations(
    limit: int | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    cases = load_eval_dataset()
    if category:
        cases = [case for case in cases if case.get("category") == category]
    if limit:
        cases = cases[:limit]

    results = []
    for case in cases:
        _clear_case_sessions(case)
        if "steps" in case:
            results.append(_evaluate_multi_step_case(case))
        else:
            results.append(_evaluate_single_step_case(case))

    total = len(results)
    passed = sum(1 for result in results if result["passed"])
    category_summary: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0})
    for result in results:
        cat = str(result.get("category", "unknown"))
        category_summary[cat]["total"] += 1
        if result["passed"]:
            category_summary[cat]["passed"] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": (passed / total) if total else 0,
        "category_summary": dict(sorted(category_summary.items())),
        "results": results,
    }
