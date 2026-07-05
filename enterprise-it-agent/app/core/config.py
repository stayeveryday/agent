from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    model_name: str = "deepseek-v4-flash"
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"
    embedding_use_fp16: bool = True
    embedding_batch_size: int = 8
    intent_provider: str = "fine_tuned"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
