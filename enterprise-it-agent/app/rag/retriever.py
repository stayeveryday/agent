from app.rag.vector_store import load_faiss_store


def _match_filters(
    department: str,
    access_level: str,
    department_filter: str | None,
    access_level_filter: str | None,
) -> bool:
    if department_filter and department != department_filter:
        return False
    if access_level_filter and access_level != access_level_filter:
        return False
    return True


def search_knowledge_base(
    query: str,
    top_k: int = 4,
    fetch_k: int = 8,
    department: str | None = None,
    access_level: str | None = None,
) -> dict[str, object]:
    store = load_faiss_store()
    matches = store.similarity_search_with_score(query, k=fetch_k)

    results = []
    for document, score in matches:
        item_department = str(document.metadata.get("department", ""))
        item_access_level = str(document.metadata.get("access_level", ""))
        if not _match_filters(
            department=item_department,
            access_level=item_access_level,
            department_filter=department,
            access_level_filter=access_level,
        ):
            continue
        results.append(
            {
                "source": str(document.metadata.get("source", "")),
                "department": item_department,
                "access_level": item_access_level,
                "length": len(document.page_content),
                "score": float(score),
                "content": document.page_content,
            }
        )
        if len(results) >= top_k:
            break

    return {
        "query": query,
        "top_k": top_k,
        "fetch_k": fetch_k,
        "department": department,
        "access_level": access_level,
        "results": results,
    }
