import argparse
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_FILE = ROOT / "data" / "intent_eval_cases.jsonl"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare LLM intent classifier with fine-tuned intent preview.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE))
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def load_cases(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
        if limit and len(cases) >= limit:
            break
    return cases


def post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_post_json(url: str, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return post_json(url, payload), None
    except HTTPError as exc:
        return None, f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}"
    except URLError as exc:
        return None, f"URL error: {exc.reason}"
    except TimeoutError:
        return None, "timeout"
    except Exception as exc:
        return None, str(exc)


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    llm_passed = sum(1 for item in results if item["llm_passed"])
    fine_tuned_intent_passed = sum(1 for item in results if item["fine_tuned_intent_passed"])
    fine_tuned_full_passed = sum(1 for item in results if item["fine_tuned_full_passed"])

    return {
        "total": total,
        "llm_intent_passed": llm_passed,
        "llm_intent_pass_rate": llm_passed / total if total else 0,
        "fine_tuned_intent_passed": fine_tuned_intent_passed,
        "fine_tuned_intent_pass_rate": fine_tuned_intent_passed / total if total else 0,
        "fine_tuned_full_passed": fine_tuned_full_passed,
        "fine_tuned_full_pass_rate": fine_tuned_full_passed / total if total else 0,
    }


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    cases = load_cases(Path(args.cases_file), args.limit)

    results = []
    for case in cases:
        question = case["query"]
        expected = case["expected"]
        expected_intent = expected["intent"]

        llm_result, llm_error = safe_post_json(
            f"{base_url}/intent",
            {"question": question},
        )
        ft_result, ft_error = safe_post_json(
            f"{base_url}/fine-tuned-intent/preview",
            {"question": question},
        )

        llm_intent = llm_result.get("intent") if llm_result else None
        ft_normalized = ft_result.get("normalized") if ft_result else None
        ft_intent = ft_normalized.get("intent") if ft_normalized else None

        ft_field_failures = []
        if ft_normalized is None:
            ft_field_failures.append("fine-tuned normalized output is missing")
        else:
            for key, value in expected.items():
                if ft_normalized.get(key) != value:
                    ft_field_failures.append(f"{key}: expected {value!r}, got {ft_normalized.get(key)!r}")

        results.append(
            {
                "name": case["name"],
                "query": question,
                "expected": expected,
                "llm_intent": llm_intent,
                "llm_error": llm_error,
                "llm_passed": llm_intent == expected_intent,
                "fine_tuned_intent": ft_intent,
                "fine_tuned_error": ft_error,
                "fine_tuned_is_valid": ft_result.get("is_valid") if ft_result else False,
                "fine_tuned_validation_failures": ft_result.get("validation_failures") if ft_result else [],
                "fine_tuned_normalized": ft_normalized,
                "fine_tuned_field_failures": ft_field_failures,
                "fine_tuned_intent_passed": ft_intent == expected_intent,
                "fine_tuned_full_passed": not ft_field_failures and not ft_error,
            }
        )

    summary = build_summary(results)
    report = {
        "summary": summary,
        "results": results,
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    report_path = ROOT / "outputs" / "ab_compare_intent_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
