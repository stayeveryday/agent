# Enterprise IT Agent Architecture

## Purpose

This project is an enterprise IT service desk Agent Harness prototype built with FastAPI, LangChain, LangGraph, local RAG, business tools, memory, approval checkpoints, trace, audit, eval, streaming, and Docker packaging.

## High-Level Flow

```text
Client
  -> FastAPI
  -> LangGraph Agent Workflow
  -> Intent classification
  -> Conditional route
      -> RAG branch
      -> Tool branch
      -> Chat branch
  -> Final answer
```

## Main Runtime Path

```text
POST /graph/run
  -> load session memory
  -> resolve user query
  -> create trace
  -> StateGraph
      -> classify_intent
      -> route_by_intent
      -> rag_route / tool_route / chat_route
      -> final_answer
  -> update session memory
  -> return AgentState
```

## Core Modules

### API

```text
app/api/routes.py
```

Owns HTTP endpoints and translates request/response schemas.

### Graph

```text
app/graph/state.py
app/graph/nodes.py
app/graph/workflow.py
app/graph/checkpoints.py
```

Owns the LangGraph state, nodes, routing, approval checkpoint, and resume logic.

### RAG

```text
app/rag/
```

Owns knowledge loading, splitting, local BGE-M3 embeddings, FAISS storage, retrieval, metadata filtering, and grounded answer generation.

### Tools

```text
app/tools/
```

Owns LangChain `StructuredTool` definitions, registry, and executor.

Current tools:

```text
get_ticket_status
create_ticket
lookup_asset
```

### Memory

```text
app/memory/store.py
```

Owns lightweight session memory:

```text
messages
last_intent
last_ticket_id
last_asset_id
last_tool_name
```

### Observability

```text
app/observability/tracing.py
```

Owns in-memory trace events for graph execution.

### Audit

```text
app/audit/log.py
```

Owns in-memory audit events for tool calls, approval requirements, checkpoints, approvals, and rejections.

### Evals

```text
data/evals/eval_dataset.jsonl
app/evals/dataset.py
app/evals/runner.py
```

Owns regression data and rule-based evaluator.

### Demo

```text
docs/demo_scenarios.md
app/demo/acceptance.py
docs/acceptance_report.md
```

Owns end-to-end demo checklist and acceptance report.

## AgentState

The graph passes one shared state object between nodes.

Important fields:

```text
trace_id
session_id
user_query
resolved_user_query
memory_context
intent
route_name
retrieved_docs
rag_sources
tool_name
tool_arguments
tool_result
approval_status
approval_checkpoint_id
final_answer
```

## RAG Flow

```text
knowledge_base markdown
  -> splitter
  -> BGEM3Embeddings
  -> FAISS
  -> search_knowledge_base
  -> retrieved_docs
  -> final_answer_node
```

## Tool Flow

```text
intent = ticket_query / asset_query / ticket_create
  -> tool_route_node
  -> build tool_name + tool_arguments
  -> run_tool
  -> tool_result
  -> final_answer_node
```

## Approval Flow

```text
ticket_create
  -> create_ticket is sensitive
  -> approval_status = pending
  -> approval_checkpoint_id
  -> approve endpoint
  -> run_tool(create_ticket)
  -> final answer
```

## Current Boundaries

This is a v0.1 learning prototype.

Known production gaps:

```text
in-memory memory, trace, audit, and checkpoint storage
mock ticket and asset tools
rule-based tool argument extraction
event-level streaming, not token streaming
Docker defaults to CPU embedding
no real authentication or authorization provider
```

## Next Production Upgrades

Recommended next upgrades:

```text
Redis/PostgreSQL for memory and checkpoint
PostgreSQL/Elasticsearch for audit logs
LangSmith or OpenTelemetry for tracing
LLM structured output for tool argument extraction
real ticket/asset system adapters
real user identity and ACL
token-level streaming
GPU-ready Docker deployment
CI pipeline for eval regression
```

