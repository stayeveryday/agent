from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.chains.chat_model import build_chat_model
from app.rag.retriever import search_knowledge_base


rag_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an enterprise IT service desk assistant. "
            "Answer in the user's language. "
            "Use the retrieved knowledge base context when it is relevant. "
            "If the context is insufficient, say what is missing instead of inventing details. "
            "Keep the answer clear, concise, and actionable.",
        ),
        (
            "user",
            "User question:\n{question}\n\n"
            "Retrieved context:\n{context}\n\n"
            "Write a helpful answer. If you use the knowledge base, mention the source ids naturally.",
        ),
    ]
)


def _format_context(results: list[dict[str, object]]) -> str:
    if not results:
        return "No matching knowledge base context was retrieved."

    blocks = []
    for index, item in enumerate(results, start=1):
        source = _get_result_source(item)
        content = _get_result_content(item)
        blocks.append(f"[{index}] Source: {source}\n{content}")
    return "\n\n".join(blocks)


def _get_result_source(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("source", ""))

    metadata = getattr(item, "metadata", {})
    if isinstance(metadata, dict):
        return str(metadata.get("source", ""))
    return ""


def _get_result_content(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("content", ""))

    return str(getattr(item, "page_content", ""))


def collect_sources(results: list[dict[str, object]]) -> list[str]:
    unique_sources: list[str] = []
    for item in results:
        source = _get_result_source(item)
        if source and source not in unique_sources:
            unique_sources.append(source)
    return unique_sources


def generate_rag_answer(question: str, results: list[dict[str, object]]) -> str:
    context = _format_context(results)
    chain = rag_answer_prompt | build_chat_model() | StrOutputParser()
    return chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )


def answer_with_rag(
    question: str,
    top_k: int = 4,
    fetch_k: int = 8,
    department: str | None = None,
    access_level: str | None = None,
) -> dict[str, object]:
    retrieval = search_knowledge_base(
        query=question,
        top_k=top_k,
        fetch_k=fetch_k,
        department=department,
        access_level=access_level,
    )
    results = retrieval["results"]
    answer = generate_rag_answer(question=question, results=results)

    return {
        "question": question,
        "top_k": top_k,
        "fetch_k": fetch_k,
        "department": department,
        "access_level": access_level,
        "answer": answer,
        "sources": collect_sources(results),
        "results": results,
    }
