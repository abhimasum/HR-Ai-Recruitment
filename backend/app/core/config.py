from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://hr:hr@localhost:5432/hr"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_provider: str = "openai"  # "openai" | "huggingface"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    accept_threshold: int = 80
    reject_threshold: int = 50


settings = Settings()
