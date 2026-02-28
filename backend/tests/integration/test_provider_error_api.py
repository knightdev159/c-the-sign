from fastapi.testclient import TestClient

from app.api.routes.assess import get_decision_agent
from app.api.routes.chat import get_chat_agent
from app.main import app
from app.services.provider_errors import ProviderConfigurationError, ProviderServiceError


class BrokenDecisionAgent:
    def assess(self, patient_id: str, top_k: int = 5) -> object:
        raise ProviderConfigurationError("Vertex generation cannot use model 'gemini-1.5-pro'.")


class BrokenChatAgent:
    def respond(self, session_id: str, message: str, top_k: int = 5) -> object:
        raise ProviderServiceError("Vertex generation failed: temporary upstream issue")


def test_assess_returns_503_for_provider_configuration_error() -> None:
    app.dependency_overrides[get_decision_agent] = lambda: BrokenDecisionAgent()
    client = TestClient(app)

    response = client.post("/assess", json={"patient_id": "PT-101"})

    assert response.status_code == 503
    assert "gemini-1.5-pro" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_chat_returns_502_for_provider_service_error() -> None:
    app.dependency_overrides[get_chat_agent] = lambda: BrokenChatAgent()
    client = TestClient(app)

    response = client.post("/chat", json={"session_id": "abc", "message": "hello"})

    assert response.status_code == 502
    assert "temporary upstream issue" in response.json()["detail"]

    app.dependency_overrides.clear()
