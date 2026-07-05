# Agent 入门

## ChatPromptTemplate 和 Message 的关系

在 LangChain 里，可以直接手写消息对象：

```python
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are an assistant."),
    HumanMessage(content=question),
]
```

也可以使用 `ChatPromptTemplate`：

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an assistant."),
        ("user", "{question}"),
    ]
)
```

可以这样理解：

- `SystemMessage`、`HumanMessage` 是更底层的消息对象
- `ChatPromptTemplate` 是更高层的模板工具

`ChatPromptTemplate` 的一个重要作用，就是帮你省掉手动定义 `SystemMessage`、`HumanMessage` 这些对象。

它不只是“少写几行代码”，还多做了两件事：

- 支持变量注入，比如 `{question}`
- 更方便接到 LangChain 的链式调用里，比如 `prompt | model | parser`

所以可以简单记成：

```text
直接用 Message 对象 = 更底层
用 ChatPromptTemplate = 更方便，也更适合 LangChain 工程化开发
```

## Embedding 和 FAISS 的关系

可以先用一句话记住：

```text
Embedding 负责把文本变成向量
FAISS 负责保存向量并做相似度检索
```

它们不是同一个东西，而是前后衔接的两层。

### 入库时序图

```text
原始文档
  -> 文档切分 chunk
  -> BGEM3Embeddings.embed_documents(...)
  -> BGE-M3 模型把每个 chunk 变成向量
  -> FAISS.from_documents(...)
  -> 建立向量索引
  -> save_local(...)
  -> 保存到本地磁盘
```

在当前项目里，对应关系是：

- `BGEM3Embeddings`：负责 embedding
- `FAISS.from_documents(...)`：负责根据向量建索引
- `build_faiss_store(...)`：负责把 embedding 和 FAISS 串起来

### 检索时序图

```text
用户问题 query
  -> BGEM3Embeddings.embed_query(...)
  -> 把 query 变成一个向量
  -> store.similarity_search_with_score(...)
  -> FAISS 在索引里找最近的向量
  -> 返回最相似的 chunk
```

这里要特别区分两件事：

- 文档向量：入库时提前算好，存进 FAISS
- 查询向量：检索时临时计算，再去和文档向量比较

### 当前项目里的调用链

入库时：

```python
embeddings = build_embeddings()
store = FAISS.from_documents(documents, embeddings)
```

检索时：

```python
store = load_faiss_store()
matches = store.similarity_search_with_score(query, k=top_k)
```

这一步里，`query` 不会直接拿字符串去搜，而是会先做 embedding，再做向量相似度匹配。

### 简单类比

可以把它理解成：

```text
Embedding = 翻译器，把文本翻译成向量语言
FAISS = 仓库 + 检索系统，保存这些向量并快速查找相似项
```

## Day 14：Tool 和 LangChain 的关系

可以先记一句最核心的话：

```text
Tool = 给大模型调用的“可控函数”
```

在普通 Python 里，我们本来就可以直接写函数：

```python
def get_ticket_status(ticket_id: str) -> dict:
    ...
```

但在 LangChain 里，如果想让这个函数进入 Agent 世界，就要再补三样东西：

1. 工具名
2. 工具描述
3. 输入参数 schema

所以 Day 14 的重点不是“会不会写函数”，而是学会把业务函数包装成 `StructuredTool`。

### 为什么要有 schema

因为大模型调工具时，不能只靠“猜参数”。

比如：

```python
class TicketStatusInput(BaseModel):
    ticket_id: str = Field(min_length=3)
```

这个 schema 的作用是：

- 告诉模型这个工具需要什么参数
- 调用前先做参数校验
- 让接口文档和调试更清楚

这和你熟悉的 Java 思路很像：

```text
Python function = Java service method
Pydantic schema = Java DTO + 参数校验
StructuredTool = 暴露给 Agent 的工具定义
```

### 当前项目里的工具层

当前 Day 14 我们已经有三类业务工具：

- `get_ticket_status`
- `create_ticket`
- `lookup_asset`

对应代码位置：

- `E:\agent\enterprise-it-agent\app\tools\ticket_tools.py`
- `E:\agent\enterprise-it-agent\app\tools\asset_tools.py`
- `E:\agent\enterprise-it-agent\app\tools\registry.py`
- `E:\agent\enterprise-it-agent\app\tools\executor.py`

### 当前项目里的调用关系

```text
tool function
  -> StructuredTool
  -> registry
  -> executor
  -> FastAPI /tools/run
```

你可以把它理解成：

```text
业务函数负责“干活”
StructuredTool 负责“让 LLM 知道怎么调用”
registry 负责“统一注册”
executor 负责“按名字执行”
```

### 它和后面的 LangGraph 是什么关系

Day 14 只是先把工具准备好。

到了后面的 LangGraph：

- Graph 先判断当前问题该走哪条路
- 如果要查工单、建工单、查资产，就调用这些 tool
- 如果是知识问题，就走 RAG

所以可以简单记成：

```text
Day 12 = RAG 能回答
Day 14 = Tool 能执行
Day 15 之后 = Graph 决定什么时候回答、什么时候执行
```

## Day 15：为什么先设计 AgentState

刚开始学 LangGraph 时，很容易把注意力放在“节点怎么连”。

但企业 Agent 更关键的问题其实是：

```text
在每一步之间，系统要保存什么信息
```

LangGraph 的节点不是各写各的临时变量，而是围绕一份共享状态工作。

所以 Day 15 的重点是先定义：

- 输入进来时 state 里有什么
- intent 识别后往 state 里写什么
- RAG 检索后往 state 里写什么
- tool 执行后往 state 里写什么
- 最终返回前从 state 里读什么

### 当前项目里的 AgentState

当前文件：

- `E:\agent\enterprise-it-agent\app\graph\state.py`

当前我们定义的核心字段有：

- `user_query`
- `intent`
- `intent_reason`
- `retrieved_docs`
- `tool_name`
- `tool_arguments`
- `tool_result`
- `final_answer`
- `department`
- `access_level`
- `approval_required`
- `approval_status`
- `error_message`

### 这些字段怎么理解

可以把它理解成一张“任务上下文表”：

```text
user_query        = 用户原始输入
intent            = 当前问题属于哪一类
retrieved_docs    = 检索到的知识片段
tool_name         = 准备调用哪个工具
tool_result       = 工具执行结果
final_answer      = 最终给用户的话
approval_*        = 是否需要人工确认
error_message     = 执行失败时留下的错误信息
```

### 为什么这一步很重要

因为后面所有 LangGraph 节点，本质上都在做两件事：

```text
读取 state
更新 state
```

所以可以先记住：

```text
Day 14 解决“系统有哪些工具”
Day 15 解决“系统运行时记住哪些状态”
Day 16 才开始“把节点连成图”
```

## Day 16：最小 StateGraph

Day 16 的目标不是一下子做复杂 Agent。

而是先跑通最小闭环：

```text
START
  -> classify_intent
  -> final_answer
  -> END
```

### 当前项目里的文件

- `E:\agent\enterprise-it-agent\app\graph\nodes.py`
- `E:\agent\enterprise-it-agent\app\graph\workflow.py`

### 节点在做什么

当前我们只有两个节点：

1. `classify_intent`
   - 读取 `user_query`
   - 调用已有的 intent classifier
   - 往 state 里写入 `intent` 和 `intent_reason`

2. `final_answer`
   - 读取 `user_query`、`intent`、`intent_reason`
   - 调用已有 chat 能力
   - 往 state 里写入 `final_answer`

### 这一天真正要学会什么

重点不是 API，而是这个执行模型：

```text
节点函数输入 = state
节点函数输出 = 要更新到 state 的字段
graph 负责把这些节点按边连接起来执行
```

所以可以把 LangGraph 节点先理解成：

```text
一个只关心“读 state / 写 state”的步骤函数
```

### 为什么 Day 16 先不接 RAG 和 Tool

因为如果一开始就把：

- intent
- routing
- RAG
- tool
- approval

全塞进去，你会更难看清 LangGraph 的核心。

所以当前顺序是：

```text
Day 15：先定义状态
Day 16：先跑通最小图
Day 17：再加条件路由
Day 18：再接 RAG
Day 19：再接 Tool
```

## Day 18：把 RAG 接进 LangGraph

Day 18 做的是把 Day 17 的 `rag_route` 从占位节点变成真正的 RAG 节点。

之前的流程是：

```text
用户问题
  -> intent = knowledge_question
  -> rag_route 占位
  -> final_answer
```

现在变成：

```text
用户问题
  -> intent = knowledge_question
  -> rag_route
  -> 检索知识库
  -> 写回 state.retrieved_docs
  -> final_answer_node
  -> 基于 retrieved_docs 生成最终回答
```

### 当前项目里的关键变化

在 `E:\agent\enterprise-it-agent\app\graph\nodes.py` 里：

```python
retrieval = search_knowledge_base(...)
```

`rag_route_node` 会把检索结果写回 state：

```text
retrieved_docs = 检索到的 chunk
rag_sources = 使用到的来源文件
```

### 为什么 final_answer_node 要使用 retrieved_docs

Graph 里更清晰的职责是：

```text
rag_route_node = 负责检索
final_answer_node = 负责生成最终回答
```

所以 RAG 分支进入 `final_answer_node` 后，会读取：

```text
state.retrieved_docs
```

再把这些 chunk 作为上下文生成回答。

可以理解成：

```text
RAG 分支：rag_route 检索，final_answer_node 回答
chat 分支：final_answer_node 才负责回答
tool 分支：Day 19 再接工具结果
```

### general 和部门过滤

当前 Graph 请求里默认有：

```text
department = general
```

这里的 `general` 不是一个真实部门，而是表示“不按部门过滤”。

所以在 `rag_route_node` 里会把 `general` 转成 `None`，再交给 RAG 检索。

这样可以避免出现：

```text
按 department=general 过滤
-> 知识库里没有 general 部门
-> 检索结果为空
```

### Day 18 的核心认知

Graph 不是替代 RAG，而是编排 RAG。

```text
Day 12：单独跑 RAG
Day 17：Graph 会分流
Day 18：Graph 的 RAG 分支真的会调用 RAG
```

## Day 19：把 Tool 接进 LangGraph

Day 19 做的是把 Day 17 的 `tool_route` 从占位节点变成真正的工具执行节点。

现在工具分支的流程是：

```text
用户问题
  -> intent = ticket_query / ticket_create / asset_query
  -> tool_route
  -> 选择工具
  -> 构造工具参数
  -> run_tool(...)
  -> 写回 state.tool_result
  -> final_answer_node 基于工具结果回答
```

### 当前工具映射

```text
ticket_query  -> get_ticket_status
asset_query   -> lookup_asset
ticket_create -> create_ticket
```

### state 里新增/使用的字段

工具执行后，Graph 会写入：

```text
tool_name      = 调用了哪个工具
tool_arguments = 工具入参
tool_result    = 工具执行结果
```

### 为什么先用规则抽取参数

当前 Day 19 先用简单规则从用户问题里提取参数：

```text
INC-1001      -> ticket_id
u10018        -> employee_id
LT-2024-018   -> asset_tag
SZ-LAPTOP-018 -> hostname
```

这样能先把 Graph 和 Tool 的调用链路跑通。

后面可以再升级成：

```text
LLM structured output 提取工具参数
```

### Day 19 的核心认知

Graph 不直接写死业务逻辑，而是编排工具层：

```text
Day 14：定义工具
Day 17：根据 intent 路由到工具分支
Day 19：工具分支真的执行工具
```

## Day 20：敏感工具需要人工确认

Day 20 做的是给创建类操作加审批门。

企业 Agent 里有一条很重要的边界：

```text
查询类工具可以直接执行
创建 / 修改 / 删除类工具通常要先确认
```

当前项目里，我们先把 `create_ticket` 当成敏感动作。

### 当前流程

未批准时：

```text
用户要求创建工单
  -> intent = ticket_create
  -> tool_route
  -> 构造 tool_name 和 tool_arguments
  -> approval_status = pending
  -> 不调用 create_ticket
  -> final_answer 提醒需要人工确认
```

批准后：

```text
用户要求创建工单
  -> /graph/run approved=true
  -> tool_route
  -> 调用 create_ticket
  -> tool_result 写入 state
  -> final_answer 基于工具结果回答
```

### 为什么这一步重要

这就是 human-in-the-loop 的雏形。

现在的实现还没有真正中断和恢复，只是用 `approved` 参数模拟确认结果。

Day 21 会继续做：

```text
checkpoint / resume
```

也就是让 graph 在审批点停住，确认后从之前的状态继续跑。

## Day 21：Checkpoint 和 Resume

Day 21 做的是把 Day 20 的审批门升级成可恢复流程。

Day 20 还是这种形态：

```text
一次请求里传 approved=true / false
```

Day 21 变成：

```text
第一次请求
  -> 发现需要审批
  -> 保存当前 state
  -> 返回 approval_checkpoint_id

审批请求
  -> 根据 approval_checkpoint_id 找回 state
  -> approve 或 reject
  -> 从保存的 tool_name / tool_arguments 继续处理
```

### 当前接口

创建待审批任务：

```text
POST /graph/run
```

如果返回：

```text
approval_status = pending
approval_checkpoint_id = ...
```

说明流程已经停在审批点。

批准继续：

```text
POST /graph/approvals/{checkpoint_id}/approve
```

拒绝执行：

```text
POST /graph/approvals/{checkpoint_id}/reject
```

### 当前实现的边界

当前 checkpoint 是内存版：

```text
服务重启后会丢失
多进程部署不共享
```

这适合学习 checkpoint/resume 的概念。

企业级系统应该换成：

```text
Redis
PostgreSQL
LangGraph checkpointer
```

### Day 21 的核心认知

审批不是简单的 if 判断。

更完整的企业 Agent 流程是：

```text
准备动作
  -> 暂停
  -> 保存状态
  -> 人工确认
  -> 恢复执行
```

## Memory 模块：Session Memory

我们补了一个正式的 Memory 模块。

它解决的是多轮对话里的上下文问题。

比如用户第一轮问：

```text
Please check ticket INC-1001 status.
```

第二轮接着问：

```text
What is its status now?
```

如果没有 memory，第二轮里的 `its` 指谁并不明确。

现在 `/graph/run` 可以传：

```json
{
  "session_id": "session-001",
  "user_query": "Please check ticket INC-1001 status."
}
```

系统会把这次会话保存到：

```text
app/memory/store.py
```

当前 memory 保存这些字段：

```text
messages
last_intent
last_ticket_id
last_asset_id
last_tool_name
```

第二轮如果继续传同一个 `session_id`：

```json
{
  "session_id": "session-001",
  "user_query": "What is its status now?"
}
```

系统会把用户问题补成：

```text
What is its status now?
Previous ticket id from session memory: INC-1001
```

这个补全后的问题会进入：

```text
resolved_user_query
```

### 当前接口

查看 memory：

```text
GET /memory/{session_id}
```

清空 memory：

```text
DELETE /memory/{session_id}
```

### Memory 和 State 的区别

可以这样理解：

```text
AgentState = 一次 graph 执行中的临时状态
Session Memory = 多轮对话之间保留下来的上下文
Checkpoint = 流程暂停后恢复执行的状态快照
```

三者不是一个东西，但会互相配合。

当前实现是内存版，服务重启会丢。

企业级后续可以换成：

```text
Redis
PostgreSQL
LangGraph checkpointer
```

## Day 22：Trace 和 Observability

Day 22 做的是让 Graph 执行过程可观察。

之前我们只能看到最终 state：

```text
intent
route_name
tool_result
final_answer
```

但企业级 Agent 还需要知道：

```text
这次请求走了哪些节点
每个节点耗时多久
路由为什么走这条分支
工具有没有被调用
审批状态是什么
```

### 当前实现

当前文件：

```text
E:\agent\enterprise-it-agent\app\observability\tracing.py
```

每次调用：

```text
POST /graph/run
```

都会生成：

```text
trace_id
```

并写入 state。

可以用这个接口查看完整 trace：

```text
GET /traces/{trace_id}
```

也可以查看最近的 trace 列表：

```text
GET /traces
```

### trace 里有什么

当前会记录：

```text
classify_intent 节点
route_by_intent 路由决策
rag_route / tool_route / chat_route 节点
final_answer 节点
```

每条事件包含：

```text
name
type
duration_ms
data
created_at
```

比如 tool 分支会记录：

```text
tool_name
tool_arguments
approval_status
has_tool_result
```

### 为什么这一步重要

企业 Agent 出问题时，不能只看最终回答。

你需要知道它到底错在：

```text
intent 识别
route 路由
RAG 检索
tool 参数
审批逻辑
最终回答
```

Trace 的价值就是把黑盒流程拆开看。

当前实现是内存版，适合学习。

企业级后续可以接：

```text
LangSmith
OpenTelemetry
日志平台
APM
```

## Day 23：Audit Log

Day 23 做的是审计日志。

Trace 和 Audit 不一样：

```text
Trace = 开发者排查流程怎么走
Audit = 企业追责业务动作谁做了什么
```

当前文件：

```text
E:\agent\enterprise-it-agent\app\audit\log.py
```

当前会记录这些动作：

```text
tool_call              工具执行
approval_required      敏感工具等待审批
checkpoint             创建待审批恢复点
approval               审批通过或拒绝
```

每条 audit event 会记录：

```text
audit_id
event_type
action
status
trace_id
session_id
approval_checkpoint_id
tool_name
tool_arguments
result
reason
created_at
```

### 当前接口

查看最近审计事件：

```text
GET /audit/events
```

查看单条审计事件：

```text
GET /audit/events/{audit_id}
```

### 为什么要有 Audit

只要 Agent 能执行工具，就必须能回答：

```text
谁触发了这个动作
执行了哪个工具
入参是什么
有没有审批
执行结果是什么
什么时候发生的
对应哪一次 trace
```

这就是企业级 Agent 和普通 demo 的一个重要区别。

当前实现是内存版，服务重启会丢。

后续企业级应该写入：

```text
PostgreSQL
Elasticsearch
SIEM / 审计平台
```

## Day 24：Eval 数据集

Day 24 做的是准备回归测试数据。

Agent 项目不能只靠手动点 Swagger 验证。

因为每次改 prompt、改路由、改工具参数抽取，都可能让旧能力退化。

Eval 数据集就是把这些关键场景固定下来。

当前文件：

```text
E:\agent\enterprise-it-agent\data\evals\eval_dataset.jsonl
```

当前有 16 条 case，覆盖：

```text
RAG
权限过滤
Tool 调用
审批
Memory 多轮
Trace
Audit
Smalltalk
```

每条 case 大概长这样：

```json
{
  "id": "tool_ticket_query_001",
  "category": "tool",
  "input": {
    "user_query": "Please check ticket INC-1001 status.",
    "session_id": "eval-tool-001"
  },
  "expected": {
    "intent": "ticket_query",
    "route_name": "tool",
    "tool_name": "get_ticket_status"
  }
}
```

### 当前接口

预览数据集：

```text
POST /evals/dataset
```

入参：

```json
{
  "limit": 5
}
```

返回：

```text
case_count
multi_step_count
category_counts
cases
```

### Day 24 的核心认知

Eval 不是为了证明模型很强。

Eval 是为了防止系统在迭代中悄悄变坏。

当前 Day 24 只准备数据。

Day 25 会继续写 evaluator：

```text
读取 eval_dataset.jsonl
逐条调用 /graph/run
检查 intent / route / tool / approval / memory / trace / audit
输出通过率和失败详情
```

## Day 25：Evaluator Runner

Day 25 做的是把 eval 数据集跑起来。

当前文件：

```text
E:\agent\enterprise-it-agent\app\evals\runner.py
```

当前接口：

```text
POST /evals/run
```

可以跑全部：

```json
{}
```

也可以只跑某一类：

```json
{
  "category": "tool"
}
```

或者限制数量：

```json
{
  "limit": 3
}
```

### 当前 evaluator 检查什么

它会检查：

```text
intent
route_name
tool_name
tool_arguments
approval_status
retrieved_docs 数量
rag_sources
approval_checkpoint_id
resolved_user_query
trace_id
audit_event
```

比如：

```json
"expected": {
  "tool_name": "get_ticket_status",
  "tool_arguments_contains": {
    "ticket_id": "INC-1001"
  }
}
```

会检查实际 state：

```text
state.tool_name == get_ticket_status
state.tool_arguments.ticket_id == INC-1001
```

### 为什么用规则评估

当前很多能力都有结构化输出：

```text
intent
route
tool
approval
trace
audit
```

这些不需要让大模型来判断，可以直接用代码判断。

这样更稳定，也更适合做回归测试。

### Day 25 的核心认知

企业 Agent 不能只靠人工试。

要能持续回答：

```text
我改了代码以后，RAG 有没有坏？
工具有没有坏？
审批有没有坏？
Memory 有没有坏？
Trace / Audit 还在不在？
```

Evaluator 就是回答这些问题的自动化工具。

## Day 26：Streaming

Day 26 做的是流式输出。

当前实现是 SSE：

```text
Server-Sent Events
```

新增接口：

```text
POST /graph/stream
```

它和 `/graph/run` 使用一样的入参：

```json
{
  "user_query": "Please check ticket INC-1001 status.",
  "session_id": "stream-001"
}
```

返回的是事件流：

```text
event: start
event: state
event: final
event: done
```

当前这是事件级 streaming：

```text
先告诉客户端开始
执行 Graph
返回状态摘要
返回最终答案
结束
```

还不是 token 级 streaming。

token 级 streaming 指模型一边生成一边吐 token，需要后面把模型调用改成 stream 模式。

当前 Day 26 的目标是先把后端 SSE 链路跑通。

## Day 27：Docker Packaging

Day 27 做的是把服务打包成 Docker 形态。

新增文件：

```text
Dockerfile
docker-compose.yml
.dockerignore
requirements.txt
docs/docker.md
```

启动命令：

```powershell
docker compose build
docker compose up
```

访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

### 为什么 Docker 里默认用 CPU embedding

你本地 Windows 虚拟环境已经能用 3080 Ti 跑 BGE-M3 embedding。

但 Docker 使用 GPU 需要额外安装：

```text
NVIDIA Container Toolkit
```

还要配置 compose 的 GPU 访问。

所以当前 Docker 版本默认：

```text
EMBEDDING_DEVICE=cpu
EMBEDDING_USE_FP16=false
```

这样普通 Docker 环境也能启动。

### 当前验证结果

已经验证：

```text
docker --version 可用
docker compose config 通过
Python compileall 通过
```

但当前机器上的 Docker Desktop Linux engine 没有启动，所以：

```text
docker compose build
```

暂时无法连接 Docker daemon。

启动 Docker Desktop 后再执行 build 即可。

### Day 27 的核心认知

Docker 不是为了替代本地开发环境。

它解决的是：

```text
服务如何被一致地打包、启动、部署
```

当前阶段先做到：

```text
一条 docker compose up 启动 FastAPI
```

后续企业级再补：

```text
GPU 容器
Redis / PostgreSQL
持久化 checkpoint
生产日志
Kubernetes
```

## Day 28：端到端演示场景

Day 28 做的是把已经完成的能力整理成可演示流程。

新增文档：

```text
E:\agent\enterprise-it-agent\docs\demo_scenarios.md
```

新增接口：

```text
GET /demo/scenarios
```

当前演示覆盖：

```text
健康检查
RAG 问答
权限过滤 RAG
查工单
查资产
创建工单待审批
审批后恢复执行
Memory 多轮追问
Trace 查看
Audit 查看
Eval 回归
SSE Streaming
```

Day 28 的核心目标不是加新能力，而是让项目可以被顺畅地展示和验收。

## Day 29：最终项目验收

Day 29 做的是把演示场景变成可执行验收。

新增文件：

```text
E:\agent\enterprise-it-agent\app\demo\acceptance.py
```

新增接口：

```text
POST /demo/acceptance
```

入参：

```json
{
  "include_slow": false,
  "write_report": true
}
```

它会检查：

```text
demo 文档是否存在
tool eval 是否通过
memory eval 是否通过
approval eval 是否通过
trace / audit eval 是否通过
审批恢复是否可用
trace 是否可查询
audit 是否可查询
SSE streaming 是否可用
```

如果 `write_report=true`，会写出：

```text
E:\agent\enterprise-it-agent\docs\acceptance_report.md
```

如果 `include_slow=true`，还会把 RAG eval 纳入验收。

Day 29 的核心意义是：

```text
项目不是“我觉得能跑”，而是有一份可执行的验收清单。
```

## Day 30：架构总结和学习复盘

Day 30 是收尾日。

新增文档：

```text
E:\agent\enterprise-it-agent\docs\architecture.md
E:\agent\enterprise-it-agent\docs\learning_review.md
```

`architecture.md` 说明：

```text
系统目标
主流程
模块边界
AgentState
RAG 流程
Tool 流程
Approval 流程
当前边界
生产级升级路线
```

`learning_review.md` 说明：

```text
30 天完成了什么
学到了哪些 LangChain / LangGraph 概念
当前能力水平
哪些地方还是 prototype
下一阶段怎么继续
微调支线怎么做
```

Day 30 的核心意义是：

```text
把项目从“写过一遍”变成“能讲清楚、能交付、能继续演进”。
```
