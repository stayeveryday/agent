import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.rag.embeddings import BGEM3Embeddings, build_embeddings


INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "faiss_index"


def _manifest_path(index_dir: Path) -> Path:
    return index_dir / "manifest.json"


def _build_manifest(
    source_files: list[str],
    embeddings: BGEM3Embeddings,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, Any]:
    return {
        "source_files": sorted(source_files),
        "embedding_model_name": embeddings.model_name,
        "embedding_device": embeddings.device,
        "embedding_use_fp16": embeddings.use_fp16,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }


def _save_manifest(index_dir: Path, manifest: dict[str, Any]) -> None:
    _manifest_path(index_dir).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@lru_cache(maxsize=1)
def _load_default_faiss_store() -> FAISS:
    embeddings = build_embeddings()
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def load_faiss_store(index_dir: Path | None = None) -> FAISS:
    if index_dir is None or index_dir == INDEX_DIR:
        return _load_default_faiss_store()

    embeddings = build_embeddings()
    return FAISS.load_local(
        str(index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def build_faiss_store(
    documents: list[Document],
    chunk_size: int,
    chunk_overlap: int,
    index_dir: Path | None = None,
) -> dict[str, Any]:
    path = index_dir or INDEX_DIR
    path.mkdir(parents=True, exist_ok=True)

    embeddings = build_embeddings()
    store = FAISS.from_documents(documents, embeddings)
    store.save_local(str(path))
    if path == INDEX_DIR:
        _load_default_faiss_store.cache_clear()

    source_files = [str(doc.metadata.get("source", "")) for doc in documents]
    manifest = _build_manifest(
        source_files=source_files,
        embeddings=embeddings,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    _save_manifest(path, manifest)

    return {
        "store": store,
        "manifest": manifest,
    }
