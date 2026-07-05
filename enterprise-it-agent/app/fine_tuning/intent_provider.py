from dataclasses import dataclass, field
from typing import Protocol
import re

from app.chains.intent_classifier import classify_intent
from app.core.config import settings
from app.fine_tuning.intent_preview import preview_fine_tuned_intent
from app.schemas.intent import IntentType


@dataclass
class IntentContract:
    intent: IntentType
    reason: str
    provider: str
    ticket_id: str | None = None
    asset_tag: str | None = None
    priority: str | None = None
    category: str | None = None
    raw_output: str | None = None
    validation_failures: list[str] = field(default_factory=list)


class IntentProvider(Protocol):
    name: str

    def classify(self, question: str) -> IntentContract:
        ...


class LlmIntentProvider:
    name = "llm"

    def classify(self, question: str) -> IntentContract:
        result = classify_intent(question)
        return IntentContract(
            intent=result.intent,
            reason=result.reason,
            provider=self.name,
        )


class FineTunedIntentProvider:
    name = "fine_tuned"

    def classify(self, question: str) -> IntentContract:
        result = preview_fine_tuned_intent(question)
        normalized = result.get("normalized") or {}
        failures = list(result.get("validation_failures") or [])
        intent = normalized.get("intent")
        if intent not in {
            "knowledge_question",
            "ticket_query",
            "ticket_create",
            "asset_query",
            "smalltalk",
        }:
            failures.append(f"invalid normalized intent: {intent!r}")
            intent = "knowledge_question"
        failures.extend(_semantic_guardrails(question=question, intent=intent))

        return IntentContract(
            intent=intent,
            reason="Classified by local fine-tuned LoRA intent model.",
            provider=self.name,
            ticket_id=normalized.get("ticket_id"),
            asset_tag=normalized.get("asset_tag"),
            priority=normalized.get("priority"),
            category=normalized.get("category"),
            raw_output=result.get("raw_output"),
            validation_failures=failures,
        )


class FallbackIntentProvider:
    name = "fallback"

    def __init__(self) -> None:
        self.fine_tuned = FineTunedIntentProvider()
        self.llm = LlmIntentProvider()

    def classify(self, question: str) -> IntentContract:
        fine_tuned_result = self.fine_tuned.classify(question)
        if not fine_tuned_result.validation_failures:
            fine_tuned_result.provider = self.name + ":fine_tuned"
            return fine_tuned_result

        llm_result = self.llm.classify(question)
        llm_result.provider = self.name + ":llm"
        llm_result.validation_failures = fine_tuned_result.validation_failures
        return llm_result


def build_intent_provider() -> IntentProvider:
    provider = settings.intent_provider.strip().lower()
    if provider == "fine_tuned":
        return FineTunedIntentProvider()
    if provider == "fallback":
        return FallbackIntentProvider()
    return LlmIntentProvider()


def classify_with_configured_provider(question: str) -> IntentContract:
    return build_intent_provider().classify(question)


def _semantic_guardrails(question: str, intent: str) -> list[str]:
    failures = []
    upper_question = question.upper()
    lower_question = question.lower()

    if re.search(r"\bINC-\d+\b", upper_question) and intent != "ticket_query":
        failures.append("question contains incident id but intent is not ticket_query")

    if re.search(r"\b(?:LAP|ASSET)-[A-Z0-9]+\b", upper_question) and intent != "asset_query":
        failures.append("question contains asset tag but intent is not asset_query")

    create_terms = ["create", "open", "new ticket", "新建", "创建", "开一个"]
    if any(term in lower_question or term in question for term in create_terms) and intent != "ticket_create":
        failures.append("question asks to create a ticket but intent is not ticket_create")

    return failures
