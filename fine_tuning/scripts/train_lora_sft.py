from pathlib import Path
import argparse

from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "Qwen/Qwen3-0.6B"
DEFAULT_TRAIN_FILE = ROOT / "data" / "intent_sft_train_v2.jsonl"
DEFAULT_VALID_FILE = ROOT / "data" / "intent_sft_valid_v2.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "qwen3-0.6b-it-intent-lora-v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a LoRA SFT adapter for IT intent extraction.")
    parser.add_argument("--train-file", default=str(DEFAULT_TRAIN_FILE))
    parser.add_argument("--valid-file", default=str(DEFAULT_VALID_FILE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--epochs", type=float, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_file = Path(args.train_file)
    valid_file = Path(args.valid_file)
    output_dir = Path(args.output_dir)

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(train_file),
            "validation": str(valid_file),
        },
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    training_args = SFTConfig(
        output_dir=str(output_dir),
        max_length=512,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        fp16=True,
        bf16=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Saved LoRA adapter to: {output_dir}")


if __name__ == "__main__":
    main()
