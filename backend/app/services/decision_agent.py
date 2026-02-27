"""Clinical decision support agent."""

from __future__ import annotations

from app.domain.patient import PatientRecord
from app.schemas.assess import AssessResponse
from app.schemas.common import CitationResponse
from app.services.llm_client import LLMClient
from app.services.safety_validator import SafetyValidator
from app.services.vector_store import VectorStore
from app.storage.patient_repository import PatientRepository


class DecisionAgent:
    """Combines patient data + retrieved NG12 chunks to form an assessment."""

    def __init__(
        self,
        patient_repo: PatientRepository,
        vector_store: VectorStore,
        llm_client: LLMClient,
        safety_validator: SafetyValidator,
        model_name: str,
    ) -> None:
        self._patient_repo = patient_repo
        self._vector_store = vector_store
        self._llm_client = llm_client
        self._safety_validator = safety_validator
        self._model_name = model_name

    def assess(self, patient_id: str, top_k: int = 5) -> AssessResponse:
        patient = self._patient_repo.get_patient(patient_id)
        if patient is None:
            raise KeyError(patient_id)

        # The retrieval query is built from structured patient features.
        query = self._build_query(patient)
        chunks = self._vector_store.query(query_text=query, top_k=top_k)

        # Lightweight deterministic baseline recommendation before LLM reasoning.
        recommendation, matched_criteria = self._recommendation(patient)
        if not chunks:
            recommendation = "insufficient_evidence"

        evidence_block = "\n".join(
            f"- [p.{chunk.page}] {chunk.document[:260]}" for chunk in chunks[: min(5, len(chunks))]
        )
        user_prompt = (
            f"Patient summary:\n{query}\n\n"
            f"Retrieved NG12 evidence:\n{evidence_block}\n\n"
            "Provide concise clinical reasoning grounded in the evidence."
        )
        reasoning = self._llm_client.generate(
            system_prompt=(
                "You are a clinical decision support assistant."
                "Use only provided evidence and avoid unsupported thresholds."
            ),
            user_prompt=user_prompt,
        )

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

    @staticmethod
    def _recommendation(patient: PatientRecord) -> tuple[str, list[str]]:
        symptoms = {s.lower() for s in patient.symptoms}

        # These sets are intentionally explicit for readability in a take-home project.
        urgent_referral = {
            "unexplained hemoptysis",
            "visible haematuria",
            "unexplained breast lump",
        }
        urgent_investigation = {
            "dysphagia",
            "persistent hoarseness",
            "iron-deficiency anaemia",
        }

        if symptoms.intersection(urgent_referral):
            return "urgent_referral", sorted(symptoms.intersection(urgent_referral))
        if symptoms.intersection(urgent_investigation):
            return "urgent_investigation", sorted(symptoms.intersection(urgent_investigation))
        return "no_urgent_action", []
