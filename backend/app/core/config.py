from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://hr:hr@localhost:5432/hr"
    database_admin_url: str = ""
    
    # LLM Settings
    llm_provider: str = "openai"  # "openai" | "vertexai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    
    # GCP Vertex AI Settings
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    
    # Embeddings & Vector Search
    embedding_provider: str = "openai"  # "openai" | "vertexai" | "huggingface"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    
    # Screening Thresholds
    accept_threshold: int = 80
    reject_threshold: int = 60
    
    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
