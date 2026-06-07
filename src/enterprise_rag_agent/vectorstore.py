import json
import math
import re
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore


class HashEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokenize(text):
            index = hash(token) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def load_kb_documents(path: Path) -> list[Document]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    documents: list[Document] = []
    for item in payload:
        documents.append(
            Document(
                id=item["id"],
                page_content=item["content"],
                metadata={
                    "title": item["title"],
                    "department": item.get("department", ""),
                    "source": item["id"],
                },
            )
        )
    return documents


def build_vector_store(path: Path, embeddings: Embeddings | None = None) -> InMemoryVectorStore:
    store = InMemoryVectorStore(embeddings or HashEmbeddings())
    documents = load_kb_documents(path)
    if documents:
        store.add_documents(documents)
    return store
