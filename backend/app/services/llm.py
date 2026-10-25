from functools import lru_cache
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


@lru_cache(maxsize=4)
def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Return configured Chat LLM instance (OpenAI or GCP Vertex AI Gemini)."""
    if settings.llm_provider == "vertexai":
        from langchain_google_vertexai import ChatVertexAI

        kwargs = {
            "model_name": settings.llm_model,
            "temperature": temperature,
        }
        if settings.gcp_project_id:
            kwargs["project"] = settings.gcp_project_id
        if settings.gcp_location:
            kwargs["location"] = settings.gcp_location

        return ChatVertexAI(**kwargs)

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key or None,
        temperature=temperature,
    )

