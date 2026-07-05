# Fine-Tuning Resources

## 1. 必看官方资料

OpenAI:

- Model optimization: https://developers.openai.com/api/docs/guides/model-optimization
- Supervised fine-tuning: https://developers.openai.com/api/docs/guides/supervised-fine-tuning

注意：

OpenAI 公开资料显示 fine-tuning platform 正在 winding down，新用户访问可能受限。因此下午实操优先走本地开源模型 LoRA 微调。

Hugging Face:

- TRL SFTTrainer: https://huggingface.co/docs/trl/sft_trainer
- TRL docs: https://huggingface.co/docs/trl/index
- PEFT LoRA: https://huggingface.co/docs/peft/package_reference/lora
- Transformers PEFT integration: https://huggingface.co/docs/transformers/peft

Unsloth:

- Fine-tuning LLMs guide: https://unsloth.ai/docs/get-started/fine-tuning-llms-guide
- LoRA hyperparameters guide: https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide

## 2. 本地需要下载的资源

### Python 包

见：

```text
requirements-finetune.txt
```

安装命令：

```powershell
cd E:\agent\fine_tuning
python -m pip install -r requirements-finetune.txt
```

### 基础模型

推荐：

```text
Qwen/Qwen3-0.6B
```

训练脚本第一次运行时会自动从 Hugging Face 下载。

也可以提前下载：

```powershell
huggingface-cli download Qwen/Qwen3-0.6B --local-dir E:\agent\models\Qwen3-0.6B
```

如果下载慢，先设置镜像或代理，再下载。

### 训练数据

已准备：

```text
data/intent_sft_train.jsonl
data/intent_sft_valid.jsonl
```

这是一个很小的教学数据集，用于训练模型把企业 IT 请求转换成结构化 JSON。

## 3. 推荐下午只下载这些

最小集合：

```text
transformers
datasets
accelerate
peft
trl
sentencepiece
protobuf
```

可选：

```text
tensorboard
```

暂时不建议一开始装：

```text
deepspeed
bitsandbytes
flash-attn
```

原因：Windows + CUDA 下这些包更容易卡环境，第一次学习先把 SFT + LoRA 跑通。

## 4. 成功标志

看到类似目录即可：

```text
outputs/qwen3-0.6b-it-intent-lora
  adapter_config.json
  adapter_model.safetensors
```

这说明你训练出来的是 LoRA adapter，不是完整大模型。
