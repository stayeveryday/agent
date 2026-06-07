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
    temperature: float = 0.0
    top_k: int = 4
    kb_path: Path = Field(default=Path("data/sample_kb.json"), alias="ENTERPRISE_AGENT_KB_PATH")
    memory_path: Path = Field(default=Path("data/memory.jsonl"), alias="ENTERPRISE_AGENT_MEMORY_PATH")
