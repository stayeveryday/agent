# 微调剩余学习计划

## 当前进度

已经完成：

```text
SFT / LoRA 概念
训练数据格式
train / valid
loss / eval_loss
LoRA 产物
推理
eval
v1 -> v2 数据迭代
contract layer
Intent Provider 抽象
```

当前结论：

```text
微调入门闭环：已完成
微调可解释可评估：基本完成
微调接入 Agent 原型：还差 3 个模块
预计剩余：4-6 小时
```

## 模块 1：输出工程化

预计时间：1-1.5 小时

状态：已完成第一版

学习目标：

```text
让微调模型输出变成 Agent 可以安全消费的结构化结果。
```

要完成：

```text
清理 <think>
只提取 JSON
schema validation
normalization
fallback
记录 raw_output / provider / failures
```

当前已有基础：

```text
scripts/intent_contract.py
scripts/agent_intent_preview.py
scripts/eval_lora.py
scripts/test_intent_contract.py
```

完成标准：

```text
任意模型原始输出
  -> extract_json
  -> normalize_intent_payload
  -> validate_intent_payload
  -> 得到稳定 IntentContract 或触发 fallback
```

当前已完成：

```text
build_intent_contract 统一入口
clean_model_output 清理 <think>
contract 快速测试
真实 v2 adapter preview
```

## 模块 2：扩大评测集

预计时间：1.5-2 小时

状态：已完成第一版

学习目标：

```text
从“4 条样例通过”升级为“有基本可信的评测覆盖”。
```

要完成：

```text
每个 intent 8-10 条
总计约 40 条 eval case
覆盖中文、英文、混合表达
覆盖边界 case
覆盖错误输入
```

建议指标：

```text
JSON 合法率
intent 准确率
字段准确率
ticket_id / asset_tag 抽取准确率
fallback 触发率
```

完成标准：

```text
eval_lora.py 可以输出更完整的指标
eval 报告可以说明模型在哪些 intent 上稳定，在哪些 case 上失败
```

当前已完成：

```text
新增 data/intent_eval_cases.jsonl
评测集扩展到 40 条
eval_lora.py 支持 --cases-file 和 --limit
eval_lora.py 输出总通过率和按 intent 分组通过率
```

当前结果：

```text
total: 40
passed: 28
failed: 12
pass_rate: 70.00%
```

按 intent：

```text
ticket_query:        8/9
ticket_create:       6/8
asset_query:         7/8
knowledge_question:  7/11
smalltalk:           0/4
```

主要失败模式：

```text
1. smalltalk 的 intent 对，但 category 不稳定，常输出 general / thankyou
2. network 和 wifi 的 category 边界不稳定
3. email 和 outlook / account 的 category 边界不稳定
4. 个别 ticket_query 表达被误判为 knowledge_question
5. 个别 ticket_create 表达被误判或 category 不准
```

## 模块 3：接入 Agent 的设计或最小实现

预计时间：1.5-2.5 小时

状态：已完成最小 preview 接口

学习目标：

```text
把微调 intent 模型和前面 30 天的 enterprise-it-agent 串起来。
```

推荐先做最小集成接口：

```text
/fine-tuned-intent/preview
```

返回：

```json
{
  "raw_output": "...",
  "normalized": {},
  "validation_failures": [],
  "route": "ticket_query"
}
```

暂时不要直接替换原来的 `classify_intent_node`。

推荐路线：

```text
先新增 preview 接口
再和原 LLM classifier 做对比
再决定是否接入 LangGraph
最后才替换默认 intent classifier
```

完成标准：

```text
enterprise-it-agent 可以通过 API 调用微调 intent preview
preview 结果能说明 route 会进入 RAG / Tool / Chat / Approval 哪条路径
```

当前已完成：

```text
enterprise-it-agent/app/fine_tuning/intent_contract.py
enterprise-it-agent/app/fine_tuning/intent_preview.py
enterprise-it-agent/app/schemas/fine_tuning.py
POST /fine-tuned-intent/preview
```

验证结果：

```text
POST http://127.0.0.1:8000/fine-tuned-intent/preview
question = Check INC-9012 status.
route = ticket_query
is_valid = true
```

## 附加模块：A/B 对比

状态：已完成第一版

新增：

```text
scripts/ab_compare_intent.py
outputs/ab_compare_intent_report.json
```

结果：

```text
total: 40
LLM intent accuracy: 40/40 = 100%
Fine-tuned intent accuracy: 38/40 = 95%
Fine-tuned full field accuracy: 28/40 = 70%
```

结论：

```text
暂时不建议直接替换原 LLM classifier。
推荐下一步做 fallback provider 或 v3 数据增强。
```

## 后续可选进阶

这些暂时不急：

```text
合并 LoRA 到基础模型
量化训练 QLoRA
更多超参数实验
上传 Hugging Face
OpenAI / API 型 fine-tuning
多卡训练
DPO / RLHF
```

## 推荐下一步

下一步做：

```text
模块 3：接入 Agent 的设计或最小实现
```

原因：

```text
模块 1 和模块 2 已经有第一版闭环，现在可以做一个 preview API，把微调模型结果接到 enterprise-it-agent 的边上。
```
