from fastapi.testclient import TestClient

from app.api.routes.chat import get_memory_store
from app.main import app
from app.storage.session_memory import ChatTurn, SessionMemoryStore


def test_chat_history_and_delete_lifecycle() -> None:
    memory_store = SessionMemoryStore()
    memory_store.append_turn("abc", ChatTurn(role="user", content="Hi"))
    memory_store.append_turn("abc", ChatTurn(role="assistant", content="Hello"))

    app.dependency_overrides[get_memory_store] = lambda: memory_store
    client = TestClient(app)

    history = client.get("/chat/abc/history")
    assert history.status_code == 200
    payload = history.json()
    assert payload["session_id"] == "abc"
    assert len(payload["history"]) == 2

    deleted = client.delete("/chat/abc")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True

    history_after = client.get("/chat/abc/history")
    assert history_after.status_code == 200
    assert history_after.json()["history"] == []

    app.dependency_overrides.clear()
