import json
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from enterprise_rag_agent.schemas import MemoryRecord


class ConversationMemory:
    def __init__(self, path: Path, vector_store: InMemoryVectorStore) -> None:
        self.path = path
        self.vector_store = vector_store
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._bootstrap()

    def _bootstrap(self) -> None:
        records = self._load_records()
        documents = [
            Document(
                id=f"memory-{idx}",
                page_content=record.summary,
                metadata={
                    "session_id": record.session_id,
                    "source_query": record.source_query,
                    "type": "memory",
                },
            )
            for idx, record in enumerate(records)
        ]
        if documents:
            self.vector_store.add_documents(documents)

    def _load_records(self) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(MemoryRecord.model_validate_json(line))
        return records

    def recall(self, session_id: str, query: str, limit: int = 3) -> list[str]:
        matches = self.vector_store.similarity_search(query, k=limit)
        memories: list[str] = []
        for match in matches:
            if match.metadata.get("type") != "memory":
                continue
            if match.metadata.get("session_id") not in {session_id, "global"}:
                continue
            memories.append(match.page_content)
        return memories

    def remember(self, record: MemoryRecord) -> None:
        self._append_record(record)
        self.vector_store.add_documents(
            [
                Document(
                    id=f"memory-{record.session_id}-{abs(hash(record.summary))}",
                    page_content=record.summary,
                    metadata={
                        "session_id": record.session_id,
                        "source_query": record.source_query,
                        "type": "memory",
                    },
                )
            ]
        )

    def _append_record(self, record: MemoryRecord) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")


def format_memories(memories: Iterable[str]) -> str:
    values = [f"- {item}" for item in memories]
    return "\n".join(values) if values else "无相关记忆"
