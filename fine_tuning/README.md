# Minimal Fine-Tuning Learning Pack

Summary:

```text
SUMMARY.md
```

Main notes:

```text
微调.md
remaining_plan.md
```

Training outputs are stored in `outputs/` locally and are intentionally ignored by Git.

目标：下午用 3080 Ti 跑通一次最小可理解的 SFT + LoRA 微调。

这次学习不追求训练出很强的模型，而是把微调链路完整走通：

```text
准备数据
  -> 选择基础模型
  -> 配置 LoRA
  -> 启动 SFT 训练
  -> 保存 adapter
  -> 加载 adapter 推理
  -> 理解什么时候该用微调，什么时候该用 RAG
```

## 推荐路线

本次先学习本地开源模型 LoRA 微调。

推荐基础模型：

```text
Qwen/Qwen3-0.6B
```

原因：

- 体积小，适合第一次学习。
- 3080 Ti 可以更稳地跑通。
- Hugging Face TRL 官方 SFTTrainer 文档也用 Qwen 0.6B 做 quick start 示例。

## 下午学习顺序

1. 看 `01_concepts.md`
2. 看 `02_resources.md`
3. 准备 Python 环境并安装 `requirements-finetune.txt`
4. 运行 `scripts/check_env.ps1`
5. 看 `data/intent_sft_train.jsonl`
6. 运行 `scripts/train_lora_sft.py`
7. 看输出目录 `outputs/qwen3-0.6b-it-intent-lora`

## 和当前 Agent 项目的关系

当前 `enterprise-it-agent` 已经用 RAG、Tool、Memory、Trace、Audit 构成了 Agent Harness。

微调不是替代 RAG。

本月最适合练的微调目标是：

- 意图分类更稳定
- 固定输出 JSON 格式
- 企业 IT 服务台回答风格更统一
- 对少量业务术语更敏感

不建议把知识库内容直接微调进模型。

企业知识仍然应该走 RAG，因为知识会变、权限要控、来源要可追踪。
