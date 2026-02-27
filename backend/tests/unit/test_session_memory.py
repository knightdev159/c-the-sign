from app.storage.session_memory import ChatTurn, SessionMemoryStore


def test_session_memory_append_and_trim() -> None:
    store = SessionMemoryStore(max_turns=3, ttl_hours=1)
    store.append_turn("session-1", ChatTurn(role="user", content="1"))
    store.append_turn("session-1", ChatTurn(role="assistant", content="2"))
    store.append_turn("session-1", ChatTurn(role="user", content="3"))
    store.append_turn("session-1", ChatTurn(role="assistant", content="4"))

    history = store.get_history("session-1")
    assert len(history) == 3
    assert history[0].content == "2"
    assert history[-1].content == "4"


def test_session_memory_clear() -> None:
    store = SessionMemoryStore()
    store.append_turn("session-2", ChatTurn(role="user", content="hello"))

    assert store.clear("session-2") is True
    assert store.get_history("session-2") == []
    assert store.clear("session-2") is False
