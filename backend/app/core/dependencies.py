"""Dependency helpers for shared services."""

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.services.chat_agent import ChatAgent
from app.services.embedding_client import EmbeddingClient
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore
from app.storage.session_memory import SessionMemoryStore


@lru_cache(maxsize=1)
def get_embedding_client() -> EmbeddingClient:
    settings = get_settings()
    return EmbeddingClient(
        provider=settings.embedding_provider,
        model_name=settings.embedding_model,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        persist_dir=Path(settings.vector_db_path),
        collection_name=settings.vector_collection,
        embedding_client=get_embedding_client(),
    )


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    settings = get_settings()
    return LLMClient(
        provider=settings.llm_provider,
        model_name=settings.llm_model,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


@lru_cache(maxsize=1)
def get_memory_store() -> SessionMemoryStore:
    return SessionMemoryStore()


@lru_cache(maxsize=1)
def get_chat_agent() -> ChatAgent:
    return ChatAgent(
        memory_store=get_memory_store(),
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
    )
