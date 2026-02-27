#!/usr/bin/env python3
"""Ingest the NG12 PDF into a local Chroma vector store."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from pypdf import PdfReader


@dataclass
class PageChunk:
    chunk_id: str
    text: str
    page: int
    section: str
    chunk_index: int


class EmbeddingClient:
    """Embedding client with Vertex AI primary path and deterministic mock fallback."""

    def __init__(self, provider: str, model_name: str, project: str | None, location: str | None) -> None:
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "vertex":
            try:
                return self._embed_vertex(texts)
            except Exception as exc:  # pragma: no cover - fallback behavior
                print(f"Vertex embedding failed: {exc}. Falling back to mock embeddings.")
        return [self._embed_mock(text) for text in texts]

    def _embed_vertex(self, texts: list[str]) -> list[list[float]]:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

        if not self.project or not self.location:
            raise ValueError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are required for provider=vertex")

        vertexai.init(project=self.project, location=self.location)
        model = TextEmbeddingModel.from_pretrained(self.model_name)
        inputs = [TextEmbeddingInput(text=t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
        outputs = model.get_embeddings(inputs)
        return [list(item.values) for item in outputs]

    @staticmethod
    def _embed_mock(text: str, size: int = 256) -> list[float]:
        """Deterministic mock embedding for local/offline development."""

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < size:
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= size:
                    break
            digest = hashlib.sha256(digest).digest()

        norm = math.sqrt(sum(v * v for v in values))
        if norm == 0:
            return values
        return [v / norm for v in values]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest NG12 PDF into Chroma")
    parser.add_argument("--pdf", type=Path, required=True, help="Path to NG12 PDF")
    parser.add_argument("--persist-dir", type=Path, default=Path("backend/data/chroma"))
    parser.add_argument("--collection", type=str, default="ng12_guideline")
    parser.add_argument("--chunk-size", type=int, default=1400)
    parser.add_argument("--chunk-overlap", type=int, default=250)
    parser.add_argument("--provider", choices=["vertex", "mock"], default="mock")
    parser.add_argument("--embedding-model", type=str, default="text-embedding-004")
    parser.add_argument("--project", type=str, default=None)
    parser.add_argument("--location", type=str, default=None)
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the collection")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("backend/data/chroma/ingestion_manifest.json"),
        help="Manifest output for reproducibility",
    )
    return parser.parse_args()


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def chunk_page(page_text: str, page_number: int, chunk_size: int, chunk_overlap: int) -> list[PageChunk]:
    text = normalize_whitespace(page_text)
    if not text:
        return []

    # Sliding window chunking keeps local context while preserving continuity via overlap.
    step = max(1, chunk_size - chunk_overlap)
    chunks: list[PageChunk] = []

    cursor = 0
    index = 0
    while cursor < len(text):
        end = min(len(text), cursor + chunk_size)
        chunk_text = text[cursor:end]
        # Deterministic chunk IDs are required for stable citations.
        chunk_id = f"ng12_{page_number:04d}_{index:02d}"
        chunks.append(
            PageChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                page=page_number,
                section=f"page_{page_number}",
                chunk_index=index,
            )
        )
        if end >= len(text):
            break
        cursor += step
        index += 1

    return chunks


def extract_chunks(pdf_path: Path, chunk_size: int, chunk_overlap: int) -> list[PageChunk]:
    reader = PdfReader(str(pdf_path))
    chunks: list[PageChunk] = []

    for page_idx, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        chunks.extend(chunk_page(page_text, page_idx, chunk_size, chunk_overlap))

    return chunks


def batched(items: Iterable[PageChunk], batch_size: int = 64) -> Iterable[list[PageChunk]]:
    batch: list[PageChunk] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF file not found: {args.pdf}")

    args.persist_dir.mkdir(parents=True, exist_ok=True)
    chunks = extract_chunks(args.pdf, args.chunk_size, args.chunk_overlap)

    if not chunks:
        raise RuntimeError("No chunks extracted from PDF")

    embedder = EmbeddingClient(
        provider=args.provider,
        model_name=args.embedding_model,
        project=args.project,
        location=args.location,
    )

    client = chromadb.PersistentClient(path=str(args.persist_dir))
    if args.reset:
        try:
            client.delete_collection(args.collection)
        except Exception:
            pass

    collection = client.get_or_create_collection(name=args.collection)

    for batch in batched(chunks):
        ids = [item.chunk_id for item in batch]
        docs = [item.text for item in batch]
        # Metadata is stored alongside embeddings to power citation rendering at query time.
        metas = [
            {
                "source": "NG12 PDF",
                "page": item.page,
                "section": item.section,
                "chunk_id": item.chunk_id,
                "chunk_index": item.chunk_index,
                "excerpt": item.text[:280],
            }
            for item in batch
        ]
        embeddings = embedder.embed(docs)
        collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    manifest = {
        "pdf": str(args.pdf),
        "collection": args.collection,
        "provider": args.provider,
        "embedding_model": args.embedding_model,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "chunk_count": len(chunks),
        "persist_dir": str(args.persist_dir),
    }
    write_manifest(args.manifest, manifest)

    print(f"Ingested {len(chunks)} chunks into '{args.collection}' at {args.persist_dir}")


if __name__ == "__main__":
    main()
