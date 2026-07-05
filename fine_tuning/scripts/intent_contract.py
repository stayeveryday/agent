import json
import re
from typing import Any


ALLOWED_INTENTS = {
    "knowledge_question",
    "ticket_query",
    "ticket_create",
    "asset_query",
    "smalltalk",
}
ALLOWED_PRIORITIES = {"low", "medium", "high", None}
ALLOWED_KEYS = {"intent", "ticket_id", "asset_tag", "priority", "category"}


def clean_model_output(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def extract_json(text: str) -> dict[str, Any] | None:
    cleaned = clean_model_output(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def normalize_intent_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = {key: payload.get(key) for key in ALLOWED_KEYS}

    intent = result.get("intent")
    if intent not in ALLOWED_INTENTS:
        result["intent"] = "knowledge_question"

    priority = result.get("priority")
    if priority not in ALLOWED_PRIORITIES:
        result["priority"] = None

    ticket_id = result.get("ticket_id")
    if isinstance(ticket_id, str):
        match = re.search(r"INC-\d+", ticket_id.upper())
        result["ticket_id"] = match.group(0) if match else None
    else:
        result["ticket_id"] = None

    asset_tag = result.get("asset_tag")
    result["asset_tag"] = str(asset_tag).strip().upper() if asset_tag else None

    category = result.get("category")
    result["category"] = str(category).strip().lower() if category else None

    if result["intent"] == "ticket_create":
        result["ticket_id"] = None
    if result["intent"] != "asset_query":
        result["asset_tag"] = None

    return result


def validate_intent_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    extra_keys = set(payload) - ALLOWED_KEYS
    if extra_keys:
        failures.append(f"unexpected keys: {sorted(extra_keys)}")

    if payload.get("intent") not in ALLOWED_INTENTS:
        failures.append(f"invalid intent: {payload.get('intent')!r}")

    if payload.get("priority") not in ALLOWED_PRIORITIES:
        failures.append(f"invalid priority: {payload.get('priority')!r}")

    if payload.get("intent") == "ticket_create" and payload.get("ticket_id") is not None:
        failures.append("ticket_create must not include ticket_id")

    if payload.get("intent") in {"knowledge_question", "smalltalk"} and payload.get("ticket_id") is not None:
        failures.append(f"{payload.get('intent')} must not include ticket_id")

    if payload.get("intent") != "asset_query" and payload.get("asset_tag") is not None:
        failures.append(f"{payload.get('intent')} must not include asset_tag")

    if payload.get("intent") == "asset_query" and not payload.get("asset_tag"):
        failures.append("asset_query should include asset_tag")

    return failures


def build_intent_contract(raw_output: str) -> dict[str, Any]:
    cleaned_output = clean_model_output(raw_output)
    extracted = extract_json(raw_output)
    if extracted is None:
        return {
            "raw_output": raw_output,
            "cleaned_output": cleaned_output,
            "extracted_json": None,
            "normalized": None,
            "validation_failures": ["output is not valid JSON"],
            "route": "fallback",
            "is_valid": False,
        }

    normalized = normalize_intent_payload(extracted)
    failures = validate_intent_payload(extracted)
    return {
        "raw_output": raw_output,
        "cleaned_output": cleaned_output,
        "extracted_json": extracted,
        "normalized": normalized,
        "validation_failures": failures,
        "route": normalized.get("intent", "fallback"),
        "is_valid": not failures,
    }
