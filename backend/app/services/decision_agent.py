"""Clinical decision support agent."""

from __future__ import annotations

from app.domain.patient import PatientRecord
from app.schemas.assess import AssessResponse
from app.schemas.common import CitationResponse
from app.services.llm_client import LLMClient
from app.services.patient_lookup_tool import PatientLookupTool
from app.services.safety_validator import SafetyValidator
from app.services.vector_store import VectorStore


class DecisionAgent:
    """Combines patient data + retrieved NG12 chunks to form an assessment."""

    def __init__(
        self,
        patient_lookup_tool: PatientLookupTool,
        vector_store: VectorStore,
        llm_client: LLMClient,
        safety_validator: SafetyValidator,
        model_name: str,
    ) -> None:
        self._patient_lookup_tool = patient_lookup_tool
        self._vector_store = vector_store
        self._llm_client = llm_client
        self._safety_validator = safety_validator
        self._model_name = model_name

    def assess(self, patient_id: str, top_k: int = 5) -> AssessResponse:
        lookup_plan = self._llm_client.plan_patient_lookup(patient_id)
        patient = self._patient_lookup_tool.invoke(lookup_plan.patient_id)
        if patient is None:
            raise KeyError(lookup_plan.patient_id)

        # The retrieval query is built from structured patient features.
        query = self._build_query(patient)
        chunks = self._vector_store.query(query_text=query, top_k=top_k)

        assessment = self._llm_client.generate_assessment(patient=patient, chunks=chunks)
        recommendation = assessment.recommendation
        matched_criteria = assessment.matched_criteria
        reasoning = assessment.reasoning

        citations = [
            CitationResponse(
                source=chunk.source,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                excerpt=chunk.excerpt,
            )
            for chunk in chunks[:3]
        ]

        safety = self._safety_validator.validate(
            answer_text=reasoning,
            chunks=chunks,
            mode="assess",
            patient=patient,
            recommendation=recommendation,
        )
        grounded = bool(citations) and safety.action != "abstain"
        if safety.action == "abstain":
            # Safety gate has the final say for clinical outputs.
            recommendation = "insufficient_evidence"
            reasoning = (
                "The agent abstained due to insufficient or conflicting support in the "
                "retrieved NG12 evidence."
            )

        return AssessResponse(
            patient_id=patient.patient_id,
            patient_name=patient.name,
            recommendation=recommendation,
            reasoning=reasoning,
            matched_criteria=matched_criteria,
            citations=citations,
            model=self._model_name,
            grounded=grounded,
            safety=safety,
        )

    @staticmethod
    def _build_query(patient: PatientRecord) -> str:
        return (
            f"Patient ID: {patient.patient_id}; age: {patient.age}; gender: {patient.gender}; "
            f"smoking history: {patient.smoking_history}; "
            f"symptoms: {', '.join(patient.symptoms)}; "
            f"symptom duration (days): {patient.symptom_duration_days}."
        )
