from pathlib import Path
import argparse
import sys

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "Qwen/Qwen3-0.6B"
DEFAULT_ADAPTER_DIR = ROOT / "outputs" / "qwen3-0.6b-it-intent-lora-v2"
SYSTEM_PROMPT = (
    "You are an enterprise IT intent extraction assistant. "
    "Return one compact JSON object only. "
    "Allowed keys: intent, ticket_id, asset_tag, priority, category. "
    "Allowed intent values: ticket_query, ticket_create, asset_query, knowledge_question, smalltalk. "
    "Allowed priority values: low, medium, high, null. "
    "Do not invent ticket_id for ticket_create. "
    "Do not add explanations, markdown, or thinking text."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference with the fine-tuned LoRA adapter.")
    parser.add_argument("query", nargs="*", help="User query to classify.")
    parser.add_argument("--adapter-dir", default=str(DEFAULT_ADAPTER_DIR))
    return parser.parse_args()


def generate(model, tokenizer, user_query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_query,
        },
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


def main() -> None:
    args = parse_args()
    adapter_dir = Path(args.adapter_dir)

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model.eval()

    user_query = " ".join(args.query).strip() or "Check ticket INC-9012 status."
    print(generate(model, tokenizer, user_query))


if __name__ == "__main__":
    main()
