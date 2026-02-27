from fastapi.testclient import TestClient

from app.api.routes.assess import get_decision_agent
from app.main import app
from app.schemas.assess import AssessResponse
from app.schemas.common import CitationResponse, SafetyResponse


class FakeDecisionAgent:
    def assess(self, patient_id: str, top_k: int = 5) -> AssessResponse:
        if patient_id == "PT-999":
            raise KeyError(patient_id)
        return AssessResponse(
            patient_id=patient_id,
            patient_name="John Doe",
            recommendation="urgent_referral",
            reasoning="Grounded reasoning",
            matched_criteria=["unexplained hemoptysis"],
            citations=[
                CitationResponse(
                    source="NG12 PDF",
                    page=10,
                    chunk_id="ng12_0010_00",
                    excerpt="Example evidence",
                )
            ],
            model="mock-model",
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


def test_assess_success() -> None:
    app.dependency_overrides[get_decision_agent] = lambda: FakeDecisionAgent()
    client = TestClient(app)

    response = client.post("/assess", json={"patient_id": "PT-101", "top_k": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "PT-101"
    assert payload["recommendation"] == "urgent_referral"
    assert payload["citations"][0]["chunk_id"] == "ng12_0010_00"

    app.dependency_overrides.clear()


def test_assess_missing_patient() -> None:
    app.dependency_overrides[get_decision_agent] = lambda: FakeDecisionAgent()
    client = TestClient(app)

    response = client.post("/assess", json={"patient_id": "PT-999"})

    assert response.status_code == 404
    assert "Patient not found" in response.json()["detail"]

    app.dependency_overrides.clear()
