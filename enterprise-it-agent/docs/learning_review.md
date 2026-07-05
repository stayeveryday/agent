# Learning Review

## Goal

The goal was to learn how to build an enterprise-grade Agent Harness with LangChain and LangGraph.

The project now demonstrates a working Enterprise IT Agent v0.1.

## What Was Built

The project now includes:

```text
FastAPI service
LangChain model calls
Prompt templates
Structured output intent classification
RAG over internal markdown knowledge base
Local BGE-M3 embeddings with FAISS
Metadata filtering
Business tools
LangGraph workflow
Conditional routing
Session memory
Human approval gate
Checkpoint/resume
Trace
Audit log
Eval dataset
Evaluator runner
SSE streaming
Docker packaging
Demo scenarios
Acceptance report
```

## Most Important Concepts Learned

### LangChain

Important abstractions:

```text
ChatModel
ChatPromptTemplate
Runnable / LCEL
Structured output
Retriever
Tool
```

### RAG

RAG is not only retrieval.

Enterprise RAG includes:

```text
loader
splitter
embedding
vector store
retriever
metadata filter
citation/source tracking
answer generation
```

### LangGraph

LangGraph is useful when the agent needs workflow state.

Key idea:

```text
node = read state -> work -> write state
```

Important graph pieces:

```text
AgentState
StateGraph
conditional edges
RAG branch
Tool branch
Approval checkpoint
Resume
```

### Agent Harness

Enterprise Agent Harness is more than an LLM call.

Current harness modules:

```text
model
prompt
RAG
tools
memory
workflow
approval
trace
audit
eval
deployment
```

## Current Capability Level

After this project, the current practical level is:

```text
LangChain: intermediate
LangGraph: entry-to-intermediate
RAG engineering: intermediate
Agent Harness design: intermediate prototype level
Enterprise readiness awareness: strong beginner-to-intermediate
```

You can now build a v0.1 enterprise Agent prototype independently.

## What Is Still Prototype-Level

These parts are intentionally lightweight:

```text
mock business systems
in-memory memory
in-memory audit
in-memory trace
in-memory checkpoint
regex-based tool argument extraction
event-level streaming
CPU Docker default
```

These are good learning scaffolds, not final production designs.

## Recommended Next Phase

The next phase should focus on production hardening:

```text
1. Replace mock tools with real API adapters
2. Move memory/checkpoint to Redis or PostgreSQL
3. Move audit to PostgreSQL or Elasticsearch
4. Add real authentication and user permissions
5. Add LangSmith or OpenTelemetry
6. Add CI eval regression
7. Upgrade tool argument extraction to structured output
8. Add token-level streaming
9. Prepare GPU Docker or deployment runbook
10. Start the minimal fine-tuning side project
```

## Minimal Fine-Tuning Side Project

Recommended scope:

```text
task = intent classification
training examples = 30 to 50
validation examples = 10
format = JSONL
goal = understand the full fine-tuning loop
```

Do not fine-tune knowledge into the model.

Use RAG for knowledge.

Use fine-tuning only for:

```text
style
classification boundaries
stable structured output
domain-specific phrasing
```

## Final Summary

This project is now a coherent Agent Harness prototype.

It can:

```text
answer knowledge questions with RAG
call business tools
pause sensitive actions for approval
resume after approval
remember session context
emit trace and audit records
run regression evals
stream graph events
produce a demo and acceptance report
```

That is the main foundation needed to continue toward enterprise-grade Agent development.

