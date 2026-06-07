from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(default="deepseek-chat", alias="OPENAI_MODEL")
    embedding_backend: str = Field(default="bge-m3", alias="EMBEDDING_BACKEND")
    embedding_model_name: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL_NAME")
    embedding_device: str = Field(default="cuda", alias="EMBEDDING_DEVICE")
    embedding_use_fp16: bool = Field(default=True, alias="EMBEDDING_USE_FP16")
    embedding_batch_size: int = Field(default=8, alias="EMBEDDING_BATCH_SIZE")
    reranker_enabled: bool = Field(default=True, alias="RERANKER_ENABLED")
    reranker_model_name: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        alias="RERANKER_MODEL_NAME",
    )
    reranker_device: str = Field(default="cuda", alias="RERANKER_DEVICE")
    reranker_use_fp16: bool = Field(default=True, alias="RERANKER_USE_FP16")
    reranker_batch_size: int = Field(default=8, alias="RERANKER_BATCH_SIZE")
    retrieval_fetch_k: int = Field(default=12, alias="RETRIEVAL_FETCH_K")
    vector_store_backend: str = Field(default="faiss", alias="VECTOR_STORE_BACKEND")
    vector_store_path: Path = Field(
        default=Path("data/faiss_index"),
        alias="VECTOR_STORE_PATH",
    )
    temperature: float = 0.0
    top_k: int = 4
    kb_path: Path = Field(default=Path("data/sample_kb.json"), alias="ENTERPRISE_AGENT_KB_PATH")
    memory_path: Path = Field(default=Path("data/memory.jsonl"), alias="ENTERPRISE_AGENT_MEMORY_PATH")
