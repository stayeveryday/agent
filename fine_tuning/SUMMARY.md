# Fine-Tuning Summary

## Goal

Learn the smallest practical fine-tuning loop and connect the result to the enterprise Agent prototype.

The target task was not knowledge injection. The target task was intent extraction for Agent routing:

```text
User query
  -> fine-tuned intent model
  -> contract layer
  -> LangGraph route
```

## Model And Method

- Base model: `Qwen/Qwen3-0.6B`
- Method: SFT with LoRA
- Main task: enterprise IT intent extraction
- Main output contract:

```json
{
  "intent": "ticket_query",
  "ticket_id": "INC-1001",
  "asset_tag": null,
  "priority": null,
  "category": "ticket"
}
```

## Dataset Versions

### v1

- Train: `data/intent_sft_train.jsonl`
- Valid: `data/intent_sft_valid.jsonl`
- Result: training completed, but eval was weak.

Observed issue:

```text
Model learned to output JSON-like text, but schema and intent values were unstable.
```

### v2

- Train: `data/intent_sft_train_v2.jsonl`
- Valid: `data/intent_sft_valid_v2.jsonl`
- Output: `outputs/qwen3-0.6b-it-intent-lora-v2`

Changes:

```text
Fixed all outputs to the same 5 fields.
Made the system prompt stricter.
Added more Chinese, English, and mixed examples.
```

Training result:

```text
train loss decreased from about 4.46 to 0.34
eval loss decreased from about 1.89 to 0.41
```

## Evaluation

Expanded eval set:

```text
data/intent_eval_cases.jsonl
```

Full eval result:

```text
Passed: 28/40 (70.00%)
```

By intent:

```text
ticket_query:        8/9
ticket_create:       6/8
asset_query:         7/8
knowledge_question:  7/11
smalltalk:           0/4
```

Main failure modes:

```text
smalltalk intent was usually right, but category was not normalized to chat.
wifi/network category boundary was unstable.
outlook/account/email category boundary was unstable.
some ticket status phrasing such as "has been resolved" was misclassified.
```

## A/B Result

Script:

```text
scripts/ab_compare_intent.py
```

Result on 40 eval cases:

```text
LLM intent accuracy:           40/40 = 100%
Fine-tuned intent accuracy:    38/40 = 95%
Fine-tuned full field accuracy: 28/40 = 70%
```

Conclusion:

```text
The original LLM classifier generalizes better for intent-only classification.
The fine-tuned model provides richer structured fields, but still needs better field-level accuracy.
```

## Agent Integration

Implemented in `enterprise-it-agent`:

```text
POST /fine-tuned-intent/preview
INTENT_PROVIDER=llm
INTENT_PROVIDER=fine_tuned
INTENT_PROVIDER=fallback
```

Files:

```text
enterprise-it-agent/app/fine_tuning/intent_contract.py
enterprise-it-agent/app/fine_tuning/intent_preview.py
enterprise-it-agent/app/fine_tuning/intent_provider.py
enterprise-it-agent/app/schemas/fine_tuning.py
```

Verified graph run with:

```text
INTENT_PROVIDER=fine_tuned
```

Example result:

```text
intent_provider = fine_tuned
intent = ticket_query
route_name = tool
tool_name = get_ticket_status
tool_arguments.ticket_id = INC-1001
```

## Important Boundary

This fine-tuned model should not replace RAG.

Recommended use:

```text
Use fine-tuning for routing, schema, extraction, and stable behavior.
Use RAG for enterprise knowledge, changing policies, permissions, and source-grounded answers.
```

## Current Recommendation

Do not fully replace the original LLM classifier yet.

Recommended mode:

```text
INTENT_PROVIDER=fallback
```

Reason:

```text
Use the fine-tuned model where it is stable.
Fallback to the LLM classifier when contract or semantic guardrails fail.
```

## Next Improvements

```text
1. Add category normalization: wifi -> network, outlook/account -> email, device -> asset.
2. Add more smalltalk training samples with category=chat.
3. Add more ticket status phrasing: resolved, progress, update, current state.
4. Train v3 and rerun eval/A-B comparison.
5. Move model serving into a separate service if productionizing.
```

