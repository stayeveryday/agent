from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from enterprise_rag_agent.memory import ConversationMemory
from enterprise_rag_agent.schemas import MemoryRecord


def test_memory_recall_and_persist(tmp_path: Path) -> None:
    store = InMemoryVectorStore(FakeEmbeddings(size=8))
    memory = ConversationMemory(tmp_path / "memory.jsonl", store)

    memory.remember(
        MemoryRecord(
            session_id="s1",
            summary="用户关注 VPN 开通流程。",
            source_query="怎么开通 VPN",
            final_answer="请提交 IT 工单。",
        )
    )

    recalled = memory.recall("s1", "VPN 怎么申请", limit=2)
    assert recalled
    assert "VPN" in recalled[0]
