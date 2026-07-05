# Current Status

## Goal

Current learning goal: become able to build an enterprise-grade Agent Harness with LangChain + LangGraph.

Current project: `E:\agent\enterprise-it-agent`

Progress status:

- Week 1 completed
- 30-day learning project completed through Day 30
- Main thread has now added final architecture summary and learning review

## Current Project State

The project already has:

- FastAPI service
- LangChain chat chain
- prompt template separation
- chain inspection endpoint
- structured intent classification
- local RAG pipeline

Deployment files:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `requirements.txt`
- `docs/docker.md`
- `docs/architecture.md`
- `docs/learning_review.md`
- `docs/demo_scenarios.md`
- `docs/acceptance_report.md`

Current app structure:

```text
app/
  audit/
    log.py
  api/
    routes.py
  chains/
    basic_chat.py
    chat_model.py
    intent_classifier.py
  core/
    config.py
  demo/
    acceptance.py
    scenarios.py
  evals/
    dataset.py
    runner.py
  prompts/
    it_support.py
  graph/
    checkpoints.py
    nodes.py
    state.py
    workflow.py
  memory/
    store.py
  observability/
    tracing.py
  streaming/
    sse.py
  rag/
    answer.py
    embeddings.py
    ingest.py
    knowledge_base.py
    preview.py
    retriever.py
    splitter.py
    vector_store.py
  tools/
    asset_tools.py
    executor.py
    registry.py
    ticket_tools.py
  schemas/
    chat.py
    demo.py
    evals.py
    graph.py
    intent.py
    memory.py
    rag.py
    tracing.py
    tools.py
    workflow.py
  main.py
```

## Running Service

Current local service:

- Health: `http://127.0.0.1:8000/health`
- Swagger: `http://127.0.0.1:8000/docs`

The service was started successfully and `/health` returned `{"status":"ok"}`.

## RAG Status

Current RAG path:

```text
markdown documents
-> loader
-> chunk splitter
-> local BGEM3 embeddings
-> FAISS local index
-> retriever
-> RAG answer chain
```

Knowledge base location:

- `E:\agent\enterprise-it-agent\data\knowledge_base`

FAISS index location:

- `E:\agent\enterprise-it-agent\data\faiss_index`

Embedding model:

- `BAAI/bge-m3`

Embedding runtime:

- local
- `cuda`
- verified on `NVIDIA GeForce RTX 3080 Ti`

PyTorch runtime status:

- `torch 2.11.0+cu128`
- `torch.cuda.is_available() == True`

Current ingest result verified:

- `document_count = 4`
- `chunk_count = 5`
- `stored_count = 5`

## Important Endpoints

General learning endpoints:

- `GET /demo/scenarios`
- `POST /demo/acceptance`
- `POST /evals/dataset`
- `POST /evals/run`
- `POST /chat`
- `POST /model-chat`
- `POST /prompt-preview`
- `POST /chain-debug`
- `POST /intent`

RAG endpoints:

- `GET /rag/preview`
- `POST /rag/preview-tuned`
- `POST /rag/ingest`
- `POST /rag/search`
- `POST /rag/answer`

Tool endpoints:

- `GET /tools`
- `POST /tools/run`

Graph learning endpoints:

- `GET /graph/state`
- `POST /graph/state/preview`
- `GET /graph/workflow`
- `POST /graph/run`
- `POST /graph/stream`
- `POST /graph/approvals/{checkpoint_id}/approve`
- `POST /graph/approvals/{checkpoint_id}/reject`

Memory endpoints:

- `GET /memory/{session_id}`
- `DELETE /memory/{session_id}`

Trace endpoints:

- `GET /traces`
- `GET /traces/{trace_id}`

Audit endpoints:

- `GET /audit/events`
- `GET /audit/events/{audit_id}`

## What Has Been Verified

Verified working:

- app import
- FastAPI startup
- local BGEM3 embedding on CUDA
- FAISS ingest
- FAISS similarity search
- first full RAG answer chain
- metadata-filtered retrieval
- first LangChain business tools
- first AgentState design for LangGraph
- first runnable minimal StateGraph
- conditional graph routing by intent
- RAG branch connected inside LangGraph
- Tool branch connected inside LangGraph
- approval gating for ticket creation
- in-memory checkpoint and approval resume endpoints
- session memory with `session_id`
- in-memory trace events for graph execution
- in-memory audit events for tool calls and approvals
- eval dataset preview and summary
- rule-based evaluator runner
- SSE event streaming for graph execution
- end-to-end demo checklist
- final acceptance runner
- final architecture and learning review docs

Observed behavior:

- `/rag/search` can retrieve correct chunks for VPN and ticket questions
- `/rag/answer` returns grounded answers and source paths

## Known Issues / Notes

1. `agent 入门.md` and some older markdown files may look garbled in PowerShell output because of terminal encoding, but file edits continued normally.
2. `CURRENT_STATUS.md` should be treated as the short recovery document if chat context gets compressed.
3. `manifest.json` in `faiss_index` stores source files and chunk parameters, but `source_files` is not deduplicated by document yet.
4. `source` is a document-level origin field, not a unique chunk identifier.
5. Current ingest is rebuild-style idempotent:
   same content does not keep appending forever, but every ingest rebuilds the full FAISS index.
6. Day 13 verification result:
   metadata filtering works, but semantic retrieval still depends on `fetch_k`.
   An unrestricted asset query did not surface the restricted asset doc in top results until access filtering narrowed the candidate set.
7. Day 14 tool harness is currently mock-data based:
   it is for learning LangChain tool abstraction first, before wiring real enterprise systems.
8. Day 15 does not build the graph yet:
   it defines the shared state contract first, which later nodes and routing will use.
9. Day 17 routes by intent:
   `knowledge_question` goes to a RAG placeholder branch; ticket and asset intents go to a tool placeholder branch; `smalltalk` goes to a chat branch.
10. Day 18 connects `rag_route`:
   knowledge questions in `/graph/run` now retrieve docs in `rag_route`, then `final_answer_node` uses `retrieved_docs` to generate the grounded answer.
11. In graph RAG retrieval, `department=general` is normalized to no department filter.
12. Day 19 connects `tool_route`:
   ticket and asset intents now build tool arguments, call the Day 14 tool executor, and write `tool_name`, `tool_arguments`, and `tool_result` into state.
13. Day 20 approval gate:
   `create_ticket` does not execute unless `/graph/run` is called with `approved=true`.
14. Day 21 checkpoint/resume:
   pending approvals from `/graph/run` now return `approval_checkpoint_id`; approval or rejection endpoints resume from the saved state.
15. Memory module:
   `/graph/run` accepts `session_id`; memory stores recent messages and last business references such as `last_ticket_id`.
   Follow-up questions can enrich `resolved_user_query` from session memory.
16. Day 22 tracing:
   `/graph/run` returns `trace_id`; `/traces/{trace_id}` shows node events, route decisions, durations, and compact outputs.
17. Day 23 audit log:
   tool calls, pending approval checkpoints, approvals, and rejections are recorded as audit events.
18. Day 24 eval dataset:
   `data/evals/eval_dataset.jsonl` has 16 cases across RAG, permission, tool, approval, memory, trace, audit, and chat.
19. Day 25 evaluator:
   `/evals/run` executes eval cases and checks actual graph state against expected rules.
   Verified categories include `tool`, `memory`, `approval`, `audit`, and `trace`.
20. Day 26 streaming:
   `/graph/stream` returns SSE events: `start`, `state`, `final`, and `done`.
21. Day 27 Docker packaging:
   Docker files package the FastAPI service and mount `./data`; compose defaults embedding to CPU.
   `docker compose config` passed. `docker compose build` needs Docker Desktop Linux engine to be running.
22. Day 28 demo scenarios:
   `docs/demo_scenarios.md` defines the end-to-end demo checklist and `/demo/scenarios` exposes it through the API.
23. Day 29 acceptance:
   `/demo/acceptance` runs the final acceptance checklist and can write `docs/acceptance_report.md`.
24. Day 30 final summary:
   `docs/architecture.md` and `docs/learning_review.md` summarize the project architecture, learning outcomes, known boundaries, and next-phase upgrades.

## Next Recommended Step

The next learning step should be:

- Start the next phase: production hardening or minimal fine-tuning

After that:

- Replace mock tools, persist memory/checkpoint/audit, add real identity/ACL, and run CI evals.
