import pytest

from app.domain.patient import PatientRecord
from app.domain.rag import RetrievedChunk
from app.services.embedding_client import EmbeddingClient
from app.services.llm_client import AssessmentDraft, LLMClient, PatientLookupPlan
from app.services.provider_errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderServiceError,
)
import app.services.vertex_auth as vertex_auth


def test_embedding_client_uses_mock_when_mock_provider_selected() -> None:
    client = EmbeddingClient(provider="mock", model_name="mock", project=None, location=None)

    embeddings = client.embed(["hello"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 256


def test_llm_client_mock_patient_lookup_plan_is_structured() -> None:
    client = LLMClient(provider="mock", model_name="mock", project=None, location=None)

    plan = client.plan_patient_lookup("PT-101")

    assert plan == PatientLookupPlan(patient_id="PT-101")


def test_llm_client_mock_assessment_uses_retrieved_evidence() -> None:
    client = LLMClient(provider="mock", model_name="mock", project=None, location=None)
    patient = PatientRecord(
        patient_id="PT-101",
        name="John Doe",
        age=55,
        gender="Male",
        smoking_history="Current Smoker",
        symptoms=["unexplained hemoptysis", "fatigue"],
        symptom_duration_days=14,
    )
    chunks = [
        RetrievedChunk(
            chunk_id="ng12_0010_00",
            document="Adults aged 40 and over with unexplained hemoptysis should be referred urgently.",
            source="NG12 PDF",
            page=10,
            section="page_10",
            distance=0.1,
            excerpt="Adults aged 40 and over with unexplained hemoptysis should be referred urgently.",
        )
    ]

    draft = client.generate_assessment(patient=patient, chunks=chunks)

    assert draft == AssessmentDraft(
        recommendation="urgent_referral",
        reasoning="Mock assessment mode found NG12 evidence supporting unexplained hemoptysis, which maps to urgent_referral.",
        matched_criteria=["unexplained hemoptysis"],
    )


def test_embedding_client_requires_vertex_project_and_location() -> None:
    client = EmbeddingClient(provider="vertex", model_name="text-embedding-004", project=None, location="us-central1")

    with pytest.raises(ProviderConfigurationError, match="GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION"):
        client.embed(["hello"])


def test_llm_client_requires_vertex_application_default_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_default(*args: object, **kwargs: object) -> tuple[None, None]:
        raise vertex_auth.DefaultCredentialsError("missing adc")

    monkeypatch.setattr(vertex_auth, "default", fake_default)
    client = LLMClient(
        provider="vertex",
        model_name="gemini-2.5-flash",
        project="cthesign",
        location="us-central1",
    )

    with pytest.raises(ProviderAuthenticationError, match="gcloud auth application-default login"):
        client.generate("system", "user")


def test_embedding_client_reports_invalid_google_application_credentials_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "D:\\cts\\key.json")
    client = EmbeddingClient(
        provider="vertex",
        model_name="text-embedding-004",
        project="cthesign",
        location="us-central1",
    )

    with pytest.raises(ProviderAuthenticationError, match="does not exist on this machine"):
        client.embed(["hello"])


def test_wrap_vertex_error_flags_retired_or_inaccessible_model() -> None:
    error = vertex_auth.wrap_vertex_error(
        provider_label="Vertex generation",
        model_name="gemini-1.5-pro",
        project="cthesign",
        location="us-central1",
        exc=RuntimeError(
            "404 Publisher Model `projects/cthesign/locations/us-central1/publishers/google/models/gemini-1.5-pro` "
            "was not found or your project does not have access to it."
        ),
    )

    assert isinstance(error, ProviderConfigurationError)
    assert "gemini-2.5-flash" in str(error)


def test_wrap_vertex_error_uses_provider_service_error_for_unknown_failure() -> None:
    error = vertex_auth.wrap_vertex_error(
        provider_label="Vertex generation",
        model_name="gemini-2.5-flash",
        project="cthesign",
        location="us-central1",
        exc=RuntimeError("temporary upstream issue"),
    )

    assert isinstance(error, ProviderServiceError)
