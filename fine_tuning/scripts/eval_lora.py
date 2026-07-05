import json
from pathlib import Path
import argparse

from infer_lora import DEFAULT_ADAPTER_DIR, MODEL_NAME, generate
from intent_contract import build_intent_contract
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_FILE = ROOT / "data" / "intent_eval_cases.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the fine-tuned LoRA adapter.")
    parser.add_argument("--adapter-dir", default=str(DEFAULT_ADAPTER_DIR))
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE))
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def load_cases(path: Path, limit: int | None = None) -> list[dict]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
        if limit and len(cases) >= limit:
            break
    return cases


def score(actual: dict | None, expected: dict) -> tuple[bool, list[str]]:
    if actual is None:
        return False, ["output is not valid JSON"]
    failures = []
    for key, value in expected.items():
        if actual.get(key) != value:
            failures.append(f"{key}: expected {value!r}, got {actual.get(key)!r}")
    return not failures, failures


def build_summary(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    by_intent: dict[str, dict[str, int]] = {}
    for item in results:
        intent = item["expected"].get("intent", "unknown")
        bucket = by_intent.setdefault(intent, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        if item["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1

    for bucket in by_intent.values():
        bucket["pass_rate"] = bucket["passed"] / bucket["total"] if bucket["total"] else 0

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0,
        "by_intent": by_intent,
    }


def main() -> None:
    args = parse_args()
    adapter_dir = Path(args.adapter_dir)
    cases = load_cases(Path(args.cases_file), args.limit)

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model.eval()

    results = []
    for case in cases:
        raw = generate(model, tokenizer, case["query"])
        contract = build_intent_contract(raw)
        actual = contract["normalized"]
        passed, failures = score(actual, case["expected"])
        failures.extend(contract["validation_failures"])
        passed = passed and not failures
        results.append(
            {
                "name": case["name"],
                "passed": passed,
                "query": case["query"],
                "expected": case["expected"],
                "actual": actual,
                "contract": contract,
                "raw": raw,
                "failures": failures,
            }
        )

    summary = build_summary(results)
    print(f"Passed: {summary['passed']}/{summary['total']} ({summary['pass_rate']:.2%})")
    print(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2))

    report_path = Path(__file__).resolve().parents[1] / "outputs" / "eval_lora_report.json"
    report_path.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
