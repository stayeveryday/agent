from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.fine_tuning.intent_contract import build_intent_contract


ROOT_DIR = Path(__file__).resolve().parents[3]
MODEL_NAME = "Qwen/Qwen3-0.6B"
ADAPTER_DIR = ROOT_DIR / "fine_tuning" / "outputs" / "qwen3-0.6b-it-intent-lora-v2"
SYSTEM_PROMPT = (
    "You are an enterprise IT intent extraction assistant. "
    "Return one compact JSON object only. "
    "Allowed keys: intent, ticket_id, asset_tag, priority, category. "
    "Allowed intent values: ticket_query, ticket_create, asset_query, knowledge_question, smalltalk. "
    "Allowed priority values: low, medium, high, null. "
    "Do not invent ticket_id for ticket_create. "
    "Do not add explanations, markdown, or thinking text."
)

_TOKENIZER: Any | None = None
_MODEL: Any | None = None


def _load_model() -> tuple[Any, Any]:
    global _TOKENIZER, _MODEL
    if _TOKENIZER is not None and _MODEL is not None:
        return _TOKENIZER, _MODEL

    if not ADAPTER_DIR.exists():
        raise RuntimeError(f"Fine-tuned adapter not found: {ADAPTER_DIR}")

    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    model.eval()

    _TOKENIZER = tokenizer
    _MODEL = model
    return tokenizer, model


def _generate_raw_output(question: str) -> str:
    tokenizer, model = _load_model()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
        )

    generated = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def preview_fine_tuned_intent(question: str) -> dict[str, Any]:
    raw_output = _generate_raw_output(question)
    contract = build_intent_contract(raw_output)
    return {
        "user_query": question,
        "provider": "qwen3_0_6b_lora_v2",
        "adapter_dir": str(ADAPTER_DIR),
        "raw_output": contract["raw_output"],
        "cleaned_output": contract["cleaned_output"],
        "extracted_json": contract["extracted_json"],
        "normalized": contract["normalized"],
        "validation_failures": contract["validation_failures"],
        "route": contract["route"],
        "is_valid": contract["is_valid"],
    }
