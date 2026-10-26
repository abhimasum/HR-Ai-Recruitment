from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "vertexai":
        from langchain_google_vertexai import VertexAIEmbeddings

        kwargs = {"model_name": settings.embedding_model}
        if settings.gcp_project_id:
            kwargs["project"] = settings.gcp_project_id
        if settings.gcp_embedding_location:
            kwargs["location"] = settings.gcp_embedding_location
        return VertexAIEmbeddings(**kwargs)

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key or None,
    )
