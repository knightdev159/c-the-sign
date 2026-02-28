import chromadb

from app.services.vector_store import VectorStore


class FakeEmbeddingClient:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class StaleCollection:
    def __init__(self) -> None:
        self.calls = 0

    def query(self, **kwargs: object) -> dict[str, list[list[object]]]:
        self.calls += 1
        raise chromadb.errors.NotFoundError("stale collection id")


class FreshCollection:
    def query(self, **kwargs: object) -> dict[str, list[list[object]]]:
        return {
            "documents": [["Example guideline text"]],
            "metadatas": [[{
                "chunk_id": "ng12_0010_00",
                "source": "NG12 PDF",
                "page": 10,
                "section": "page_10",
                "excerpt": "Example excerpt",
            }]],
            "distances": [[0.12]],
        }


class FakeClient:
    def __init__(self, refreshed_collection: FreshCollection) -> None:
        self.refreshed_collection = refreshed_collection
        self.collection_name_requested: str | None = None

    def get_collection(self, name: str) -> FreshCollection:
        self.collection_name_requested = name
        return self.refreshed_collection


def test_vector_store_refreshes_collection_after_chroma_reset() -> None:
    store = VectorStore.__new__(VectorStore)
    store._collection_name = "ng12_guideline"
    store._embedding_client = FakeEmbeddingClient()
    store._collection = StaleCollection()
    fresh_collection = FreshCollection()
    store._client = FakeClient(refreshed_collection=fresh_collection)

    chunks = store.query("What does NG12 say?", top_k=3)

    assert store._client.collection_name_requested == "ng12_guideline"
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "ng12_0010_00"
    assert chunks[0].page == 10
