from dataclasses import dataclass, field
from typing import Protocol
import re

from intent_contract import normalize_intent_payload, validate_intent_payload


@dataclass
class IntentContract:
    intent: str
    ticket_id: str | None = None
    asset_tag: str | None = None
    priority: str | None = None
    category: str | None = None
    provider: str = "unknown"
    raw_output: str | None = None
    validation_failures: list[str] = field(default_factory=list)


class IntentProvider(Protocol):
    def classify(self, question: str) -> IntentContract:
        ...


class RuleBasedIntentProvider:
    name = "rule_based"

    def classify(self, question: str) -> IntentContract:
        upper_question = question.upper()
        lower_question = question.lower()
        ticket_match = re.search(r"INC-\d+", upper_question)
        if ticket_match:
            return IntentContract(
                intent="ticket_query",
                ticket_id=ticket_match.group(0),
                category="ticket",
                provider=self.name,
            )

        if "LAP-" in upper_question or "ASSET-" in upper_question:
            asset_match = re.search(r"(?:LAP|ASSET)-[A-Z0-9]+", upper_question)
            return IntentContract(
                intent="asset_query",
                asset_tag=asset_match.group(0) if asset_match else None,
                category="asset",
                provider=self.name,
            )

        if "create" in lower_question or "新建" in question or "创建" in question:
            priority = "medium"
            if "high" in lower_question or "高优先级" in question:
                priority = "high"
            elif "low" in lower_question or "低优先级" in question:
                priority = "low"

            category = "network" if "network" in lower_question or "wifi" in lower_question else "general"
            return IntentContract(
                intent="ticket_create",
                priority=priority,
                category=category,
                provider=self.name,
            )

        return IntentContract(
            intent="knowledge_question",
            category="general",
            provider=self.name,
        )


class FineTunedIntentProvider:
    name = "fine_tuned_lora"

    def classify(self, question: str) -> IntentContract:
        # Demo only: in real code, this would call the local LoRA model.
        raw_payload = {
            "intent": "ticket_create" if "create" in question.lower() else "knowledge_question",
            "ticket_id": "INC-9999",
            "asset_tag": None,
            "priority": "medium",
            "category": "network",
        }
        normalized = normalize_intent_payload(raw_payload)
        failures = validate_intent_payload(raw_payload)
        return IntentContract(
            **normalized,
            provider=self.name,
            raw_output=str(raw_payload),
            validation_failures=failures,
        )


class FallbackIntentProvider:
    def __init__(self, providers: list[IntentProvider]) -> None:
        self.providers = providers

    def classify(self, question: str) -> IntentContract:
        last_result: IntentContract | None = None
        for provider in self.providers:
            result = provider.classify(question)
            if not result.validation_failures:
                return result
            last_result = result

        return last_result or IntentContract(
            intent="knowledge_question",
            category="general",
            provider="fallback_default",
            validation_failures=["all providers failed"],
        )


def main() -> None:
    provider = FallbackIntentProvider(
        [
            FineTunedIntentProvider(),
            RuleBasedIntentProvider(),
        ]
    )
    for question in [
        "Create a medium priority network ticket. Meeting room wifi is down.",
        "Check INC-3002 for me.",
        "Find asset owner for LAP-1200.",
    ]:
        print(question)
        print(provider.classify(question))
        print()


if __name__ == "__main__":
    main()
