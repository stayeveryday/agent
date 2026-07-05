from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document


KB_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge_base"


DOC_METADATA = {
    "asset_lookup_policy.md": {
        "department": "it_asset",
        "doc_type": "policy",
        "access_level": "restricted",
    },
    "email_login_reset.md": {
        "department": "it_support",
        "doc_type": "troubleshooting",
        "access_level": "standard",
    },
    "ticket_status_guide.md": {
        "department": "service_desk",
        "doc_type": "guide",
        "access_level": "standard",
    },
    "vpn_troubleshooting.md": {
        "department": "network",
        "doc_type": "troubleshooting",
        "access_level": "standard",
    },
}


def load_knowledge_base() -> list[Document]:
    loader = DirectoryLoader(
        str(KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    documents = loader.load()
    for document in documents:
        source = Path(str(document.metadata.get("source", "")))
        metadata = DOC_METADATA.get(source.name, {})
        document.metadata["source"] = str(source)
        document.metadata["department"] = metadata.get("department", "general")
        document.metadata["doc_type"] = metadata.get("doc_type", "note")
        document.metadata["access_level"] = metadata.get("access_level", "standard")
    return documents
