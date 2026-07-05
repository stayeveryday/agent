import argparse
import json
from pathlib import Path

from infer_lora import DEFAULT_ADAPTER_DIR, MODEL_NAME, generate
from intent_contract import build_intent_contract
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview how fine-tuned intent output would enter the Agent.")
    parser.add_argument("query", nargs="*", help="User query to classify.")
    parser.add_argument("--adapter-dir", default=str(DEFAULT_ADAPTER_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    adapter_dir = Path(args.adapter_dir)
    user_query = " ".join(args.query).strip() or "Check ticket INC-9012 status."

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model.eval()

    raw = generate(model, tokenizer, user_query)
    contract = build_intent_contract(raw)

    preview = {
        "user_query": user_query,
        "raw_model_output": contract["raw_output"],
        "cleaned_model_output": contract["cleaned_output"],
        "extracted_json": contract["extracted_json"],
        "normalized_for_agent": contract["normalized"],
        "validation_failures": contract["validation_failures"],
        "agent_route": contract["route"],
        "is_valid": contract["is_valid"],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
