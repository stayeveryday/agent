from app.rag.knowledge_base import load_knowledge_base
from app.rag.splitter import split_documents
from app.rag.vector_store import build_faiss_store


def ingest_knowledge_base(
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> dict[str, int | str | bool]:
    documents = load_knowledge_base()
    chunks = split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    result = build_faiss_store(
        chunks,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    manifest = result["manifest"]
    stored = len(chunks)

    gpu_available = False
    try:
        import torch

        gpu_available = bool(torch.cuda.is_available())
    except Exception:
        gpu_available = False

    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "stored_count": stored,
        "embedding_model_name": str(manifest["embedding_model_name"]),
        "embedding_device": str(manifest["embedding_device"]),
        "gpu_available": gpu_available,
    }
