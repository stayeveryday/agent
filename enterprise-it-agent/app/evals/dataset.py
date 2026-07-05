import json
from collections import Counter
from pathlib import Path
from typing import Any


DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "evals" / "eval_dataset.jsonl"


def load_eval_dataset(limit: int | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
            items.append(item)
            if limit and len(items) >= limit:
                break
    return items


def summarize_eval_dataset() -> dict[str, object]:
    items = load_eval_dataset()
    category_counts = Counter(str(item.get("category", "unknown")) for item in items)
    multi_step_count = sum(1 for item in items if "steps" in item)
    return {
        "dataset_path": str(DATASET_PATH),
        "case_count": len(items),
        "multi_step_count": multi_step_count,
        "category_counts": dict(sorted(category_counts.items())),
    }


def preview_eval_dataset(limit: int = 5) -> dict[str, object]:
    return {
        **summarize_eval_dataset(),
        "cases": load_eval_dataset(limit=limit),
    }
