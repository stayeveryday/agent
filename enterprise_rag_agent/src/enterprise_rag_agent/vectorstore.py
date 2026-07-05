import json
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS


class BGEM3Embeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
        use_fp16: bool = True,
        batch_size: int = 8,
    ) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as exc:
            raise RuntimeError(
                "FlagEmbedding is not installed. Run `pip install FlagEmbedding torch` "
                "inside the project's virtual environment."
            ) from exc

        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.batch_size = batch_size
        self._model = BGEM3FlagModel(
            model_name,
            use_fp16=use_fp16,
            device=device,
        )

    def _encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: list[list[float]] = []
        for index in range(0, len(texts), self.batch_size):
            batch = texts[index : index + self.batch_size]
            result: dict[str, Any] = self._model.encode(
                batch,
                batch_size=len(batch),
                max_length=8192,
            )
            dense_vecs = result["dense_vecs"]
            payload.extend(dense_vecs.tolist())
        return payload

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text])[0]


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


def _build_manifest(kb_path: Path, embeddings: BGEM3Embeddings) -> dict[str, Any]:
    return {
        "kb_path": str(kb_path.resolve()),
        "kb_mtime": kb_path.stat().st_mtime,
        "embedding_model_name": embeddings.model_name,
        "embedding_device": embeddings.device,
        "embedding_use_fp16": embeddings.use_fp16,
    }


def _manifest_path(index_dir: Path) -> Path:
    return index_dir / "manifest.json"


def _should_rebuild(index_dir: Path, manifest: dict[str, Any]) -> bool:
    if not index_dir.exists():
        return True

    if not (index_dir / "index.faiss").exists():
        return True

    if not (index_dir / "index.pkl").exists():
        return True

    manifest_file = _manifest_path(index_dir)
    if not manifest_file.exists():
        return True

    current = json.loads(manifest_file.read_text(encoding="utf-8"))
    return current != manifest


def _save_manifest(index_dir: Path, manifest: dict[str, Any]) -> None:
    _manifest_path(index_dir).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_vector_store(
    path: Path,
    embeddings: BGEM3Embeddings,
    backend: str = "faiss",
    index_dir: Path | None = None,
) -> VectorStore:
    if backend != "faiss":
        raise ValueError(
            f"Unsupported vector store backend: {backend}. Only `faiss` is currently implemented."
        )

    if index_dir is None:
        raise ValueError("`index_dir` is required when using the `faiss` backend.")

    index_dir.mkdir(parents=True, exist_ok=True)
    manifest = _build_manifest(path, embeddings)

    if _should_rebuild(index_dir, manifest):
        documents = load_kb_documents(path)
        store = FAISS.from_documents(documents, embeddings)
        store.save_local(str(index_dir))
        _save_manifest(index_dir, manifest)
        return store

    return FAISS.load_local(
        str(index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )
