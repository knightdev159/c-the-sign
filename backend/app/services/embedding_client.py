"""Embedding client abstraction."""

from __future__ import annotations

import hashlib
import math


class EmbeddingClient:
    """Embeddings provider with Vertex AI primary and deterministic mock fallback."""

    def __init__(self, provider: str, model_name: str, project: str | None, location: str | None) -> None:
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "vertex":
            try:
                return self._embed_vertex(texts)
            except Exception:
                pass
        return [self._embed_mock(text) for text in texts]

    def _embed_vertex(self, texts: list[str]) -> list[list[float]]:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

        if not self.project or not self.location:
            raise ValueError("project and location are required for Vertex embeddings")

        vertexai.init(project=self.project, location=self.location)
        model = TextEmbeddingModel.from_pretrained(self.model_name)
        inputs = [TextEmbeddingInput(text=t, task_type="RETRIEVAL_QUERY") for t in texts]
        outputs = model.get_embeddings(inputs)
        return [list(item.values) for item in outputs]

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
