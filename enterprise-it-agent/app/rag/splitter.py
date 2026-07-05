from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_text_splitter(
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )


def split_documents(
    documents: list[Document],
    chunk_size: int = 400,
    chunk_overlap: int = 80,
) -> list[Document]:
    splitter = build_text_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)
