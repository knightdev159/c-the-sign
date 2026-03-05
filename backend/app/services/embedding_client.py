"""Embedding client abstraction."""

from __future__ import annotations

import hashlib
import math

from app.services.vertex_auth import ensure_vertex_access, wrap_vertex_error

import vertexai
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel


class EmbeddingClient:
    """Embeddings provider with Vertex AI primary and deterministic mock fallback."""

    def __init__(self, provider: str, model_name: str, project: str | None, location: str | None) -> None:
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "vertex":
            return self._embed_vertex(texts)
        return [self._embed_mock(text) for text in texts]

    def _embed_vertex(self, texts: list[str]) -> list[list[float]]:
        ensure_vertex_access(
            project=self.project,
            location=self.location,
            provider_label="Vertex embeddings",
        )

        try:
            vertexai.init(project=self.project, location=self.location)
            model = TextEmbeddingModel.from_pretrained(self.model_name)
            inputs = [TextEmbeddingInput(text=t, task_type="RETRIEVAL_QUERY") for t in texts]
            outputs = model.get_embeddings(inputs)
            return [list(item.values) for item in outputs]
        except Exception as exc:
            raise wrap_vertex_error(
                provider_label="Vertex embeddings",
                model_name=self.model_name,
                project=self.project,
                location=self.location,
                exc=exc,
            ) from exc

    @staticmethod
    def _embed_mock(text: str, size: int = 256) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < size:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= size:
                    break
            digest = hashlib.sha256(digest).digest()

        norm = math.sqrt(sum(v * v for v in values))
        return [v / norm for v in values] if norm else values
