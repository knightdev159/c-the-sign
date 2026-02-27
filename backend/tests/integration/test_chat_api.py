from fastapi.testclient import TestClient

from app.api.routes.chat import get_chat_agent
from app.main import app
from app.schemas.chat import ChatResponse
from app.schemas.common import CitationResponse, SafetyResponse


class FakeChatAgent:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def respond(self, session_id: str, message: str, top_k: int = 5) -> ChatResponse:
        self.messages.append(message)
        text = "Follow-up acknowledged" if len(self.messages) > 1 else "Initial response"
        return ChatResponse(
            session_id=session_id,
            answer=text,
            citations=[
                CitationResponse(
                    source="NG12 PDF",
                    page=22,
                    chunk_id="ng12_0022_01",
                    excerpt="Evidence",
                )
            ],
            grounded=True,
            safety=SafetyResponse(
                action="allow",
                groundedness_score=1.0,
                evidence_coverage=1.0,
                rule_consistency="unknown",
                unsupported_claims=[],
                conflicts=[],
                notes=[],
            ),
        )


def test_chat_multi_turn_follow_up() -> None:
    fake_agent = FakeChatAgent()
    app.dependency_overrides[get_chat_agent] = lambda: fake_agent
    client = TestClient(app)

    first = client.post("/chat", json={"session_id": "abc", "message": "First question"})
    second = client.post("/chat", json={"session_id": "abc", "message": "What about under 40?"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["answer"] == "Follow-up acknowledged"

    app.dependency_overrides.clear()


def test_chat_response_includes_safety_block() -> None:
    fake_agent = FakeChatAgent()
    app.dependency_overrides[get_chat_agent] = lambda: fake_agent
    client = TestClient(app)

    response = client.post("/chat", json={"session_id": "xyz", "message": "What does NG12 say about cough?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["safety"]["action"] == "allow"
    assert "citations" in payload

    app.dependency_overrides.clear()
