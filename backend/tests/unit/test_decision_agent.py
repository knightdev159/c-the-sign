from app.domain.patient import PatientRecord
from app.domain.rag import RetrievedChunk
from app.schemas.common import SafetyResponse
from app.services.decision_agent import DecisionAgent
from app.services.llm_client import AssessmentDraft, PatientLookupPlan


class FakePatientLookupTool:
    def __init__(self, patient: PatientRecord | None) -> None:
        self._patient = patient
        self.requested_ids: list[str] = []

    def invoke(self, patient_id: str) -> PatientRecord | None:
        self.requested_ids.append(patient_id)
        return self._patient


class FakeVectorStore:
    def query(self, query_text: str, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id="ng12_0010_00",
                document="Unexplained hemoptysis warrants urgent referral.",
                source="NG12 PDF",
                page=10,
                section="page_10",
                distance=0.1,
                excerpt="Unexplained hemoptysis warrants urgent referral.",
            )
        ]


class FakeLLMClient:
    def __init__(self) -> None:
        self.lookup_requests: list[str] = []
        self.assessment_requests: list[tuple[PatientRecord, list[RetrievedChunk]]] = []

    def plan_patient_lookup(self, requested_patient_id: str) -> PatientLookupPlan:
        self.lookup_requests.append(requested_patient_id)
        return PatientLookupPlan(patient_id=requested_patient_id)

    def generate_assessment(self, *, patient: PatientRecord, chunks: list[RetrievedChunk]) -> AssessmentDraft:
        self.assessment_requests.append((patient, chunks))
        return AssessmentDraft(
            recommendation="no_urgent_action",
            reasoning="The model-controlled assessment returned no urgent action.",
            matched_criteria=["unexplained hemoptysis"],
        )


class FakeSafetyValidator:
    def validate(self, **kwargs: object) -> SafetyResponse:
        return SafetyResponse(
            action="allow",
            groundedness_score=1.0,
            evidence_coverage=1.0,
            rule_consistency="unknown",
            unsupported_claims=[],
            conflicts=[],
            notes=[],
        )


def test_decision_agent_uses_lookup_tool_and_model_assessment() -> None:
    patient = PatientRecord(
        patient_id="PT-101",
        name="John Doe",
        age=55,
        gender="Male",
        smoking_history="Current Smoker",
        symptoms=["unexplained hemoptysis"],
        symptom_duration_days=14,
    )
    lookup_tool = FakePatientLookupTool(patient)
    llm_client = FakeLLMClient()
    agent = DecisionAgent(
        patient_lookup_tool=lookup_tool,
        vector_store=FakeVectorStore(),
        llm_client=llm_client,
        safety_validator=FakeSafetyValidator(),
        model_name="mock-model",
    )

    response = agent.assess("PT-101", top_k=3)

    assert llm_client.lookup_requests == ["PT-101"]
    assert lookup_tool.requested_ids == ["PT-101"]
    assert response.recommendation == "no_urgent_action"
    assert response.matched_criteria == ["unexplained hemoptysis"]
    assert response.reasoning == "The model-controlled assessment returned no urgent action."


def test_decision_agent_raises_for_missing_patient_from_lookup_tool() -> None:
    agent = DecisionAgent(
        patient_lookup_tool=FakePatientLookupTool(None),
        vector_store=FakeVectorStore(),
        llm_client=FakeLLMClient(),
        safety_validator=FakeSafetyValidator(),
        model_name="mock-model",
    )

    try:
        agent.assess("PT-999")
    except KeyError as exc:
        assert exc.args[0] == "PT-999"
    else:
        raise AssertionError("Expected KeyError for missing patient")
