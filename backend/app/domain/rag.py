"""RAG-related domain models."""

from pydantic import BaseModel


class Citation(BaseModel):
    source: str
    page: int
    chunk_id: str
    excerpt: str


class RetrievedChunk(BaseModel):
    chunk_id: str
    document: str
    source: str
    page: int
    section: str | None = None
    distance: float | None = None
    excerpt: str

    def to_citation(self) -> Citation:
        return Citation(
            source=self.source,
            page=self.page,
            chunk_id=self.chunk_id,
            excerpt=self.excerpt,
        )
