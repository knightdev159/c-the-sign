"""Vector store access layer backed by Chroma."""

from __future__ import annotations

from pathlib import Path

import chromadb

from app.domain.rag import RetrievedChunk
from app.services.embedding_client import EmbeddingClient


class VectorStore:
    """Persistent Chroma collection used by both assess and chat workflows."""

    def __init__(self, persist_dir: Path, collection_name: str, embedding_client: EmbeddingClient) -> None:
        self._collection_name = collection_name
        self._embedding_client = embedding_client
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def query(self, query_text: str, top_k: int = 5) -> list[RetrievedChunk]:
        # Retrieval uses query embeddings so assess/chat share identical vector behavior.
        query_embedding = self._embedding_client.embed([query_text])[0]
        try:
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except chromadb.errors.NotFoundError:
            self._collection = self._client.get_collection(name=self._collection_name)
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[RetrievedChunk] = []
        for doc, meta, distance in zip(docs, metas, distances):
            metadata = meta or {}
            # Normalize Chroma rows into a strict internal model for downstream safety/citations.
            chunks.append(
                RetrievedChunk(
                    chunk_id=str(metadata.get("chunk_id", "")),
                    document=str(doc),
                    source=str(metadata.get("source", "NG12 PDF")),
                    page=int(metadata.get("page", 0) or 0),
                    section=str(metadata.get("section")) if metadata.get("section") else None,
                    distance=float(distance) if distance is not None else None,
                    excerpt=str(metadata.get("excerpt", doc[:280])),
                )
            )

        return chunks
