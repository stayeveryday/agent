# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install the package (editable)
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test
pytest tests/test_memory.py -v

# Run the interactive demo (requires OPENAI_API_KEY)
python demo.py

# Required env vars
set OPENAI_API_KEY=your_key
set OPENAI_MODEL=gpt-4o-mini           # default
set OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # default
```

## Architecture

LangGraph-based RAG agent with 8 sequential nodes:

```
recall_memory → rewrite_query → detect_intent → retrieve_docs → invoke_tools → summarize → reflect → write_memory
```

- **agent.py** — `StateGraph` definition, all 8 node functions, and agent builder. Orchestrates the full pipeline.
- **config.py** — `AgentSettings` (pydantic-settings), reads from env vars and `.env` file.
- **schemas.py** — `AgentState` (TypedDict) for graph state, plus structured output models (`RewriteResult`, `IntentResult`, `ReflectionResult`, `MemoryRecord`).
- **prompts.py** — System prompts for each node, in Chinese.
- **vectorstore.py** — KB document loading from JSON + `InMemoryVectorStore` construction.
- **memory.py** — `ConversationMemory` class: persists to JSONL, recalls via vector similarity search.
- **tools.py** — Two example tools: `current_time` and `create_helpdesk_ticket` (fake).

### Default stack

| Layer | Default | Replaceable with |
|---|---|---|
| LLM | ChatOpenAI (gpt-4o-mini) | Any LangChain chat model |
| Embeddings | OpenAIEmbeddings | Any embedding model |
| Vector store | InMemoryVectorStore | Milvus, PGVector, ES, Weaviate |
| Memory | JSONL file | Redis, Postgres |
| Tools | current_time, create_helpdesk_ticket | Real enterprise APIs (ticket, CRM, ERP) |

### State flow

`AgentState` flows through all nodes. Key decisions happen at `detect_intent` (sets `needs_retrieval` and `needs_tools` booleans). `retrieve_docs` and `invoke_tools` skip if their respective flags are false. `reflect` adds a `follow_up_question` to `final_answer` if confidence is low. `write_memory` compresses the turn into a memory record and persists it.
