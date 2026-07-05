# LangChain + LangGraph 企业级 Agent Harness 30 天学习计划

## 目标

在 30 天内掌握基于 LangChain + LangGraph 开发企业级 Agent 的主干能力，并完成一个可演示的企业 IT 服务台 Agent v0.1。

本计划面向已有 5 年 Java 后端经验、并有 Java RAG 开发经验的学习者。学习重点不是从零理解 RAG 或 LLM，而是掌握 Agent Harness 的工程结构，以及如何用 LangChain + LangGraph 将 RAG、工具调用、状态管理、人工审批、观测、评估和服务化串成一个完整系统。

本月新增一条轻量支线目标：学会最简单的模型微调。这里的“学会”不是深入训练大模型，而是掌握一次监督微调 SFT 的完整闭环：准备数据、转换 JSONL、提交训练或本地 LoRA、对比基座模型和微调模型、写出适用边界。

## 一个月后应达到的水平

- LangChain：中级。
- LangGraph：入门到中级。
- Agent Harness：中级理解。
- 企业 Agent 工程：能独立实现 v0.1 原型。
- 生产级治理：知道关键问题在哪里，能继续补强。

一个月后应能做到：

- 熟练使用 LangChain 的核心抽象：ChatModel、Prompt、Runnable、Tool、Retriever、Structured Output。
- 能用 LangGraph 设计有状态 workflow。
- 能实现一个企业 Agent Harness 原型。
- 能接入 RAG、业务 API、人工审批、流式输出。
- 能用 LangSmith 做 trace 和调试。
- 能写 FastAPI 服务对外暴露 Agent。
- 能解释 agent harness 的关键模块和工程边界。
- 能判断什么场景适合 Agent，什么场景应该使用确定性 workflow。
- 能完成一次最小模型微调实验，知道微调适合解决什么问题，也知道什么时候不该微调。

## 核心项目

本计划围绕一个项目推进：

**企业 IT 服务台 Agent v0.1**

功能目标：

- 用户自然语言提问。
- 检索内部知识库。
- 查询工单状态。
- 创建工单。
- 查询用户资产。
- 判断是否需要升级人工。
- 涉及创建、关闭、变更类操作时要求人工确认。
- 所有工具调用有审计日志。
- 所有回答带 trace。
- 支持流式响应。
- 支持多轮会话。
- 支持评估集回归测试。

## 模型微调支线目标

本月微调目标保持轻量，不和 Agent Harness 主线抢时间。

目标不是训练一个强模型，而是跑通最简单的监督微调闭环：

```text
准备样例数据
  ↓
整理为 JSONL
  ↓
划分训练集 / 验证集
  ↓
提交一次 SFT 或本地 LoRA
  ↓
对比 base model 和 tuned model
  ↓
记录适用场景、成本和风险
```

推荐选一个非常小的场景：

- 意图分类：把用户输入分类为 `knowledge_question`、`ticket_query`、`ticket_create`、`asset_query`、`smalltalk`。
- 输出风格：让模型稳定输出企业 IT 服务台风格的简短回答。
- 结构化输出：让模型更稳定地产生指定 JSON schema。

不建议第一个月做这些：

- 用微调替代 RAG。
- 把企业知识库内容直接灌进微调数据。
- 做 RLHF、DPO、RFT 等进阶训练。
- 训练大规模开源模型。

最小验收标准：

- 准备 30 到 50 条训练样例。
- 准备 10 条验证 / 对比样例。
- 至少跑通一次训练流程，或在无法使用托管微调时跑通一次本地 LoRA dry run。
- 写一份对比记录：base model 输出、tuned model 输出、是否真的改善、是否值得继续。

注意：不同平台支持的微调模型、权限和价格变化较快。实际执行前要查当时的官方文档。如果使用 OpenAI，先确认当前账号是否能创建 fine-tuning job；如果不方便使用托管微调，可以用 Hugging Face + PEFT/LoRA 做本地最小实验。

## Agent Harness 心智模型

企业级 Agent 可以拆成：

```text
企业级 Agent
= LLM
+ Tools
+ Memory / State
+ RAG
+ Workflow
+ Permission
+ Human Approval
+ Observability
+ Evaluation
+ Deployment
```

需要掌握的 10 个模块：

1. Model Adapter：屏蔽不同模型提供商差异，统一 chat、stream、tool calling、structured output。
2. Prompt Layer：管理 system prompt、few-shot、prompt version、动态上下文注入。
3. Tool Registry：注册业务 API、数据库查询、搜索、RAG、工单系统、CRM 等工具。
4. Tool Executor：处理 timeout、retry、error mapping、audit log、敏感操作审批。
5. State / Memory：保存任务状态、会话记忆、用户偏好、工作流中间结果。
6. RAG Layer：检索、rerank、citation、metadata filter、ACL 权限过滤。
7. Planner / Router：识别意图、选择 workflow、决定是否调用工具或进入人工确认。
8. Guardrails：输入过滤、输出校验、Schema 校验、防 prompt injection、敏感操作拦截。
9. Observability：trace、token 成本、latency、tool call 记录、failure reason、用户反馈。
10. Evaluation：RAG 命中率、answer faithfulness、tool call accuracy、workflow success rate、regression test。

## 学习方式

不要从头刷 LangChain 文档。采用项目牵引式学习：

```text
我要实现一个功能
  ↓
先设计接口和目录
  ↓
只查当天需要的 LangChain / LangGraph 文档
  ↓
写一个最小可运行版本
  ↓
跑通
  ↓
记录 3 条总结
```

避免这种方式：

```text
打开 LangChain 文档
从 Overview 看到 Integrations
看了 3 小时
什么都没写
```

## 每日时间安排

平时每天 1 到 2 小时，建议按 1.5 小时规划：

```text
20 分钟：读官方文档 / API 示例
60 分钟：写代码
10 分钟：记录问题和当天总结
```

周末可学习 1.5 天，建议每个周末投入 10 到 12 小时：

```text
1 小时：补文档和概念
3 到 4 小时：集中开发
30 分钟：重构、测试、写 README
```

## 技术栈

- LangChain：模型、prompt、tool、retriever、structured output、Runnable。
- LangGraph：状态机、workflow、agent loop、checkpoint、human-in-the-loop。
- LangSmith：trace、debug、evaluation。
- FastAPI：对外提供企业服务接口。
- PostgreSQL / Redis：会话、checkpoint、任务状态。
- Vector DB：Milvus、Qdrant、pgvector、Elasticsearch 或 Chroma。
- OpenTelemetry：对接企业观测体系。
- Docker / Kubernetes：部署。

## 推荐项目目录

```text
enterprise-it-agent/
  app/
    api/
      chat.py
      approvals.py
    core/
      config.py
      logging.py
      tracing.py
    graph/
      state.py
      nodes.py
      edges.py
      workflow.py
    rag/
      ingest.py
      retriever.py
      prompts.py
    tools/
      registry.py
      executor.py
      ticket_tools.py
      asset_tools.py
      permissions.py
    evals/
      dataset.jsonl
      evaluators.py
    schemas/
      intent.py
      response.py
      approval.py
  docs/
    architecture.md
    runbook.md
  docker-compose.yml
  README.md
```

## 第 1 周：LangChain 核心抽象 + 项目骨架

目标：不被 Python 和 LangChain API 卡住，跑通最小后端服务。

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Day 1 | 06-29 | 搭环境 | 建 Python 项目、虚拟环境、`.env`、依赖、目录结构 | 能运行 `python -m app.main` 或 FastAPI 服务 |
| Day 2 | 06-30 | ChatModel | 接入一个模型，封装 `llm_client.py` | 能完成普通问答和流式输出 |
| Day 3 | 07-01 | Prompt | 使用 `ChatPromptTemplate`，拆 system/user prompt | prompt 可独立维护 |
| Day 4 | 07-02 | LCEL / Runnable | 写 `prompt | model | parser` pipeline | 能输出普通文本结果 |
| Day 5 | 07-03 | Structured Output | 用 Pydantic 定义意图识别结果 | 能稳定输出 JSON 结构 |
| Day 6 | 07-04 | FastAPI | 做最小接口：`/chat`、`/stream` | curl 能调通流式接口 |
| Day 7 | 07-05 | 项目整理 | 整理项目骨架、配置、日志、README | 项目像一个后端服务，而不是 demo |

第 1 周结束时要能讲清楚：

- ChatModel 解决什么问题。
- PromptTemplate 解决什么问题。
- Runnable / LCEL 的组合方式是什么。
- Structured Output 为什么对企业 Agent 很重要。

## 第 2 周：企业 RAG + Tool Harness

目标：把已有 Java RAG 经验迁移到 LangChain，并接入工具执行体系。

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Day 8 | 07-06 | 文档入库 | 准备 10 到 20 篇模拟企业知识库文档 | 有可检索语料 |
| Day 9 | 07-07 | 切分 | 实现 loader + splitter | 能看到 chunk 和 metadata |
| Day 10 | 07-08 | 向量库 | 接入 Chroma、Qdrant 或 pgvector | 文档可向量检索 |
| Day 11 | 07-09 | Retriever | 封装 `KnowledgeRetriever` | 输入问题返回 top-k 文档 |
| Day 12 | 07-10 | RAG 回答 | prompt 拼接 context，回答带引用 | 输出包含来源 |
| Day 13 | 07-11 | 权限过滤 | 加 metadata filter：部门、权限、文档类型 | 不同用户看到不同结果 |
| Day 14 | 07-12 | 业务工具 | 定义 tools：查工单、建工单、查资产 | tool 可被单独测试 |

第 2 周结束时应完成：

```text
RAG = retriever + prompt + model + citation
Tool Harness = tool schema + executor + permission check + audit log
```

重点不是重新学习 RAG，而是把 RAG 工程经验映射到 LangChain 抽象。

## 第 3 周：LangGraph Agent Harness

目标：从 demo agent 升级为可控、有状态、可恢复的企业流程。

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Day 15 | 07-13 | State 设计 | 定义 `AgentState`：user、query、intent、docs、tool_results、final_answer | state 字段清晰 |
| Day 16 | 07-14 | 基础 Graph | 写 `StateGraph`，节点：入口、意图识别、最终回答 | graph 能跑通 |
| Day 17 | 07-15 | 条件路由 | 根据 intent 分流：RAG、tool、chat | 不同问题走不同路径 |
| Day 18 | 07-16 | RAG 节点 | 把第 2 周 RAG 接入 graph | 知识问题走 RAG |
| Day 19 | 07-17 | Tool 节点 | 把查工单、查资产接入 graph | 业务问题调用工具 |
| Day 20 | 07-18 | 人工审批 | 加 human-in-the-loop：创建工单前 interrupt | 敏感操作暂停等待确认 |
| Day 21 | 07-19 | Checkpoint | 加 checkpoint，支持恢复会话 | 审批后能继续执行 |

第 3 周要完成核心工作流：

```text
用户输入
  ↓
意图识别
  ↓
条件路由
  ↓
RAG / Tool / 普通问答
  ↓
是否需要人工审批
  ↓
最终回复
```

这是整个月最关键的一周。完成后，你就从“调用 LLM”进入了“企业 Agent Harness”。

## 第 4 周：观测、评估、服务化

目标：让项目接近企业可演示状态。

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Day 22 | 07-20 | Trace | 接入 LangSmith tracing | 每次调用能看到链路 |
| Day 23 | 07-21 | Audit | 记录 tool call：用户、工具、参数、结果、耗时 | 有审计日志 |
| Day 24 | 07-22 | Eval 数据集 | 准备 30 条测试样例：RAG、tool、拒答、审批 | 有 `eval_dataset.jsonl` |
| Day 25 | 07-23 | Evaluator | 写规则评估：是否有引用、是否调用正确工具、是否误操作 | 能跑本地评估 |
| Day 26 | 07-24 | Streaming | Graph 最终结果接入 SSE 流式输出 | 前端或 curl 能实时看到输出 |
| Day 27 | 07-25 | Docker 化 | API、向量库、Redis/Postgres Docker 化 | 一条命令启动 |
| Day 28 | 07-26 | 端到端整理 | 做一次端到端重构和补测试 | 核心链路有测试 |

## 模型微调支线安排

微调支线穿插在第 2 到第 4 周，不单独占用整周时间。每次控制在 1 到 2 小时。

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Fine-tune 1 | 07-09 | 明确场景 | 选择一个最小微调任务，建议选“意图分类”或“结构化输出” | 写清楚为什么这个任务适合微调 |
| Fine-tune 2 | 07-14 | 准备数据 | 准备 30 到 50 条训练样例、10 条验证样例，整理为 JSONL | 数据能被脚本校验通过 |
| Fine-tune 3 | 07-21 | 跑通训练 | 使用 OpenAI/Azure 托管微调，或用 Hugging Face PEFT/LoRA 做本地最小实验 | 至少完成一次训练 job 或 dry run |
| Fine-tune 4 | 07-24 | 对比评估 | 用同一批 10 条样例对比 base model 和 tuned model | 写出是否改善、是否值得继续 |

微调支线最终产物：

```text
fine-tuning/
  data/
    train.jsonl
    validation.jsonl
  scripts/
    validate_dataset.py
    run_finetune.md
  reports/
    comparison.md
```

微调学习重点：

- 数据质量比训练技巧更重要。
- 微调更适合固化格式、语气、分类边界和稳定行为。
- RAG 更适合注入外部知识和保持知识更新。
- Agent Harness 中，微调模型通常是一个可替换的 Model Adapter，而不是整个系统的中心。

## 最后 2 天：验收和复盘

| 天数 | 日期 | 目标 | 具体任务 | 验收 |
| --- | --- | --- | --- | --- |
| Day 29 | 07-27 | 项目验收 | 跑 10 个真实场景：知识问答、查工单、创建工单、审批、拒答 | 全链路可演示 |
| Day 30 | 07-28 | 总结输出 | 写架构文档、技术复盘、后续路线 | 能 30 分钟讲清楚项目 |

## 最终验收标准

30 天结束时，应能现场演示：

1. 用户问知识库问题，Agent 检索并带引用回答。
2. 用户问工单状态，Agent 调工具查询。
3. 用户要求创建工单，Agent 暂停等待人工确认。
4. 人工确认后，Graph 从 checkpoint 恢复继续执行。
5. LangSmith 能看到 trace。
6. eval 能检测 RAG、tool call、审批逻辑是否退化。
7. FastAPI + Docker 能启动服务。

## 第一天开始方式

第一天不要大规模看文档，先建最小项目。

```powershell
mkdir enterprise-it-agent
cd enterprise-it-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install langchain langchain-openai langgraph langsmith fastapi uvicorn python-dotenv pydantic pydantic-settings
```

建议先建目录：

```text
enterprise-it-agent/
  app/
    main.py
    core/
      config.py
    chains/
      basic_chat.py
    schemas/
  .env
  README.md
```

第一天只实现：

```http
POST /chat
{
  "question": "我的电脑无法访问内网系统怎么办？"
}
```

返回：

```json
{
  "answer": "..."
}
```

第一天只看这些文档主题：

- Chat models。
- Prompt templates。
- Output parsers。
- LCEL / Runnable。

第一天验收：

- FastAPI 能启动。
- `/chat` 能返回模型回答。
- 能说清楚 `prompt | model | parser` 是什么。
- README 里记录当天踩的坑。

第二天再进入结构化意图识别：

```text
knowledge_question
ticket_query
ticket_create
asset_query
smalltalk
```

这一步就是 Agent Harness 的第一层：Router / Intent Classifier。

## 推荐官方文档入口

- LangChain Docs: https://docs.langchain.com/
- LangChain Agents: https://docs.langchain.com/oss/python/langchain/agents
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph Interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- LangSmith Evaluation: https://docs.langchain.com/langsmith/evaluation

## 后续补强方向

完成 v0.1 后，继续补强：

- 大规模生产环境稳定性。
- 复杂权限模型和数据隔离。
- 高质量离线评估体系。
- 多租户成本控制。
- 大规模 tool registry。
- 长任务恢复和并发调度。
- 企业级安全红队测试。
- 多 agent 协作治理。
