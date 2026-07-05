# Enterprise IT Agent

Day 1 target: run the smallest LangChain + FastAPI service.

## Setup

```powershell
cd E:\agent\enterprise-it-agent
.\.venv\Scripts\Activate.ps1
```

Create `.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=your_openai_compatible_base_url_optional
MODEL_NAME=deepseek-v4-flash
```

## Run

```powershell
uvicorn app.main:app --reload
```

## Test

```powershell
curl.exe -X POST http://127.0.0.1:8000/chat `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"我的电脑无法访问内网系统怎么办？\"}"
```

## Day 1 Notes

- `prompt | model | parser` means prompt assembly, model invocation, and output parsing are composed into one runnable chain.
- Today we only need `/chat`; RAG, tools, LangGraph, and streaming come later.

## Day 2 Notes

- `/model-chat` calls `ChatOpenAI` directly with raw messages.
- `/chat` calls `ChatPromptTemplate | ChatOpenAI | StrOutputParser`.
- Use `/model-chat` to understand the model layer alone.
- Use `/chat` to understand prompt assembly plus parsing.

## Day 3 Notes

- Prompts now live in `app/prompts/it_support.py`.
- `ChatPromptTemplate` is a reusable component, not just an inline string.
- `/prompt-preview` shows the rendered messages before they are sent to the model.
- Try `style=default`, `style=brief`, and `style=guided` to see how prompt wording changes behavior.

## Day 4 Notes

- `/chain-debug` shows the pipeline step by step.
- `prompt_messages` is the rendered prompt output.
- `model_response_content` is the raw model reply before parsing.
- `parsed_output` is the final string after `StrOutputParser`.

## Day 5 Notes

- `app/schemas/intent.py` defines the structured output contract.
- `/intent` returns a typed intent instead of plain text.
- `PydanticOutputParser` turns model JSON into a Pydantic object.
- This is the first building block for routing in an agent workflow.

## Day 6 Notes

- `app/api/routes.py` now owns the FastAPI endpoints.
- `app/schemas/chat.py` now owns request and response DTOs.
- `app/main.py` is reduced to app creation plus router registration.
- This is the first step from a demo file toward a service-style project structure.

## Day 7 Notes

- Week 1 is complete: model call, prompt template, chain inspection, structured output, and basic service structure are all in place.
- `ChatOpenAI` is the model adapter.
- `ChatPromptTemplate` is the prompt assembly layer.
- `prompt | model | parser` is the core LangChain pipeline pattern.
- FastAPI request and response models now live in `app/schemas`.

## Week 1 Summary

At the end of Week 1, the project can:

- run a FastAPI service
- call a chat model directly
- build prompts with reusable templates
- inspect the `prompt -> model -> parser` pipeline
- return structured intent classification results
- expose endpoints through a small service-style layout

Current project structure:

```text
app/
  api/
    routes.py
  chains/
    basic_chat.py
    chat_model.py
    intent_classifier.py
  core/
    config.py
  prompts/
    it_support.py
  schemas/
    chat.py
    intent.py
  main.py
```

What each part does:

- `api` holds FastAPI routes
- `chains` holds LangChain logic
- `core` holds config
- `prompts` holds reusable prompt templates
- `schemas` holds request, response, and structured output models

## Week 2 Day 8 Notes

- `app/rag/knowledge_base.py` loads markdown files from `data/knowledge_base`.
- `app/rag/splitter.py` splits documents into chunks with overlap.
- `/rag/preview` lets us inspect how many documents and chunks we have.
- Week 2 starts with document loading and chunking before vector storage.

## Week 2 Day 9 Notes

- `chunk_size` and `chunk_overlap` are now tunable inputs.
- `/rag/preview-tuned` lets us compare different chunking strategies.
- Day 9 is about understanding how chunk parameters change retrieval inputs before we add embeddings.

## Week 2 Day 10 Notes

- `app/rag/embeddings.py` now uses local `BGEM3Embeddings`.
- `app/rag/vector_store.py` now persists a local `FAISS` index.
- `app/rag/ingest.py` loads, splits, embeds, and stores chunks in the FAISS index.
- `/rag/ingest` is the first full `documents -> chunks -> embeddings -> vector store` path.

## Week 2 Day 11 Notes

- `app/rag/retriever.py` now performs FAISS similarity search.
- `/rag/search` returns top-k chunk matches for a query.
- Day 11 is where the vector store becomes a retriever instead of just an index file.

## Week 2 Day 12 Notes

- `app/rag/answer.py` now combines retrieval plus model answering.
- `/rag/answer` returns a grounded answer together with retrieved sources.
- Day 12 is the first full RAG answer chain in the project.

## Week 2 Day 13 Notes

- knowledge base documents now carry `department`, `doc_type`, and `access_level` metadata.
- `/rag/search` and `/rag/answer` now support simple metadata filtering.
- Day 13 introduces the difference between relevant retrieval and allowed retrieval.

## Week 2 Day 14 Notes

- `app/tools` is the start of the business tool harness layer.
- tools are defined as LangChain `StructuredTool` objects with explicit input schemas.
- `/tools` lists available tools and `/tools/run` lets us test each tool independently.
- Day 14 is where the project starts separating `RAG answers` from `business actions`.

## Week 3 Day 15 Notes

- `app/graph/state.py` defines the shared `AgentState` for future LangGraph workflows.
- Day 15 is about deciding what the agent must remember between nodes before building the graph itself.
- `/graph/state` explains the purpose of each state field.
- `/graph/state/preview` shows the initial state object for a new user request.

## Week 3 Day 16 Notes

- `app/graph/workflow.py` now builds the first minimal `StateGraph`.
- The first graph is intentionally small: `START -> classify_intent -> final_answer -> END`.
- `/graph/workflow` explains the nodes and edges.
- `/graph/run` executes the graph and returns the final state object.

## Week 3 Day 17 Notes

- `app/graph/workflow.py` now uses `add_conditional_edges` after intent classification.
- `knowledge_question` routes to `rag_route`.
- `ticket_query`, `ticket_create`, and `asset_query` route to `tool_route`.
- `smalltalk` and fallback cases route to `chat_route`.
- The route nodes are placeholders today; Day 18 connects the RAG branch and Day 19 connects the tool branch.

## Week 3 Day 18 Notes

- `rag_route` now retrieves knowledge chunks and writes them into state.
- Knowledge questions inside `/graph/run` now retrieve documents, apply metadata filters, and let `final_answer` generate an answer from `retrieved_docs`.
- `retrieved_docs` stores the chunks used by the graph.
- `rag_sources` stores unique source files used by the answer.
- `department=general` is treated as no department filter for graph RAG retrieval.

## Week 3 Day 19 Notes

- `tool_route` now connects to the Day 14 business tool layer.
- `ticket_query` routes to `get_ticket_status`.
- `asset_query` routes to `lookup_asset`.
- `ticket_create` routes to `create_ticket`.
- `tool_name`, `tool_arguments`, and `tool_result` are written into graph state before `final_answer` responds.

## Week 3 Day 20 Notes

- `create_ticket` now requires approval inside the graph.
- `/graph/run` accepts `approved`.
- When `approved=false`, `ticket_create` prepares `tool_name` and `tool_arguments`, sets `approval_status=pending`, and does not execute the tool.
- When `approved=true`, `ticket_create` executes `create_ticket` and writes `tool_result`.

## Week 3 Day 21 Notes

- Pending approvals now create an in-memory `approval_checkpoint_id`.
- `/graph/approvals/{checkpoint_id}/approve` resumes the pending tool call and executes it.
- `/graph/approvals/{checkpoint_id}/reject` rejects the pending action without executing the tool.
- This is a lightweight checkpoint/resume model for learning; production systems should persist checkpoints in Redis/PostgreSQL or LangGraph checkpointers.

## Week 3 Memory Notes

- `app/memory/store.py` adds a lightweight in-memory session store.
- `/graph/run` accepts `session_id`.
- Session memory stores recent messages, `last_intent`, `last_ticket_id`, `last_asset_id`, and `last_tool_name`.
- Follow-up questions can use session memory to enrich `resolved_user_query`.
- `/memory/{session_id}` reads the current session memory.
- `DELETE /memory/{session_id}` clears the current session memory.

## Week 4 Day 22 Notes

- `app/observability/tracing.py` adds lightweight in-memory tracing.
- `/graph/run` now creates a `trace_id` and returns it in graph state.
- Each graph node records a trace event with duration and compact output fields.
- `route_by_intent` records the selected route.
- `/traces` lists recent traces and `/traces/{trace_id}` returns a full trace.

## Week 4 Day 23 Notes

- `app/audit/log.py` adds lightweight in-memory audit logging.
- Tool calls are recorded as audit events.
- Pending approval checkpoints are recorded as audit events.
- Approval and rejection decisions are recorded as audit events.
- `/audit/events` lists recent audit events and `/audit/events/{audit_id}` returns one event.

## Week 4 Day 24 Notes

- `data/evals/eval_dataset.jsonl` contains the first regression dataset.
- The dataset covers RAG, permission filtering, tools, approvals, memory, tracing, and audit events.
- `app/evals/dataset.py` loads, validates, summarizes, and previews the dataset.
- `/evals/dataset` returns dataset counts and sample cases.
- Day 24 prepares the data foundation for Day 25 evaluators.

## Week 4 Day 25 Notes

- `app/evals/runner.py` runs rule-based regression checks against the eval dataset.
- `/evals/run` executes eval cases through the graph and compares actual state with expected fields.
- Evaluator checks intent, route, tool selection, tool arguments, approval status, RAG sources, memory resolution, trace, and audit events.
- `category` can be used to run a focused subset such as `tool`, `memory`, `approval`, `audit`, or `trace`.
- Day 25 moves the project from manual Swagger testing to repeatable regression testing.

## Week 4 Day 26 Notes

- `app/streaming/sse.py` adds Server-Sent Events streaming for graph execution.
- `/graph/stream` accepts the same request body as `/graph/run`.
- The stream emits `start`, `state`, `final`, and `done` events.
- This is event-level streaming; token-level model streaming can be added later.

## Week 4 Day 27 Notes

- `Dockerfile` packages the FastAPI service.
- `docker-compose.yml` exposes the service on port `8000`.
- `requirements.txt` captures runtime dependencies.
- `.dockerignore` excludes local virtualenv, logs, and development-only files.
- `docs/docker.md` documents build and run commands.
- Docker defaults embedding to CPU; local Windows CUDA remains the recommended development path for the 3080 Ti.

## Week 4 Day 28 Notes

- `docs/demo_scenarios.md` contains the end-to-end demo checklist.
- `/demo/scenarios` exposes the demo checklist through the API.
- Demo coverage includes health, RAG, permission-scoped RAG, tools, approval/resume, memory, trace, audit, eval, and streaming.
- Day 28 turns the project from a set of features into a coherent demo flow.

## Week 4 Day 29 Notes

- `app/demo/acceptance.py` runs the final acceptance checklist.
- `/demo/acceptance` executes core demo checks and can write `docs/acceptance_report.md`.
- Acceptance covers demo docs, tool eval, memory eval, approval eval, trace/audit eval, approval resume, trace lookup, audit lookup, and streaming.
- Pass `include_slow=true` to include RAG eval in the acceptance run.

## Week 4 Day 30 Notes

- `docs/architecture.md` summarizes the final system architecture.
- `docs/learning_review.md` summarizes the learning outcomes, current capability level, prototype boundaries, and next phase.
- The 30-day LangChain + LangGraph Agent Harness learning project is complete.
