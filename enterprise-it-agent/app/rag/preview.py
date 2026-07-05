from app.rag.knowledge_base import load_knowledge_base
from app.rag.splitter import split_documents


def preview_chunks(
    limit: int = 5,
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> dict[str, object]:
    documents = load_knowledge_base()
    chunks = split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    preview_items = []
    for chunk in chunks[:limit]:
        preview_items.append(
            {
                "source": chunk.metadata.get("source", ""),
                "department": chunk.metadata.get("department", ""),
                "access_level": chunk.metadata.get("access_level", ""),
                "length": len(chunk.page_content),
                "content": chunk.page_content,
            }
        )

    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "chunks": preview_items,
    }
