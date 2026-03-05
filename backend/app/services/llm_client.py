"""LLM client with Vertex AI primary and mock fallback."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.domain.patient import PatientRecord
from app.domain.rag import RetrievedChunk
from app.services.patient_lookup_tool import PatientLookupTool
from app.services.provider_errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderServiceError,
)
from app.services.vertex_auth import ensure_vertex_access, wrap_vertex_error

import vertexai
from vertexai.generative_models import FunctionDeclaration, GenerativeModel, Tool


class PatientLookupPlan(BaseModel):
    """Structured output for the patient lookup tool-selection step."""

    patient_id: str = Field(pattern=r"^PT-\d{3}$")


class AssessmentDraft(BaseModel):
    """Structured assessment returned by the reasoning model."""

    recommendation: Literal[
        "urgent_referral",
        "urgent_investigation",
        "no_urgent_action",
        "insufficient_evidence",
    ]
    reasoning: str = Field(min_length=1)
    matched_criteria: list[str] = Field(default_factory=list)


class LLMClient:
    def __init__(self, provider: str, model_name: str, project: str | None, location: str | None) -> None:
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "vertex":
            return self._generate_vertex(system_prompt, user_prompt)
        return self._generate_mock(system_prompt, user_prompt)

    def plan_patient_lookup(self, requested_patient_id: str) -> PatientLookupPlan:
        if self.provider == "vertex":
            return self._plan_patient_lookup_vertex(requested_patient_id)
        return PatientLookupPlan(patient_id=requested_patient_id)

    def generate_assessment(self, *, patient: PatientRecord, chunks: list[RetrievedChunk]) -> AssessmentDraft:
        if not chunks:
            return AssessmentDraft(
                recommendation="insufficient_evidence",
                reasoning="No relevant NG12 evidence was retrieved for this patient.",
                matched_criteria=[],
            )

        if self.provider == "vertex":
            return self._generate_assessment_vertex(patient=patient, chunks=chunks)
        return self._generate_assessment_mock(patient=patient, chunks=chunks)

    def _generate_vertex(self, system_prompt: str, user_prompt: str) -> str:
        ensure_vertex_access(
            project=self.project,
            location=self.location,
            provider_label="Vertex generation",
        )

        try:
            vertexai.init(project=self.project, location=self.location)
            model = GenerativeModel(self.model_name)
            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            if hasattr(response, "text") and response.text:
                return response.text
            return ""
        except Exception as exc:
            raise wrap_vertex_error(
                provider_label="Vertex generation",
                model_name=self.model_name,
                project=self.project,
                location=self.location,
                exc=exc,
            ) from exc

    def _plan_patient_lookup_vertex(self, requested_patient_id: str) -> PatientLookupPlan:
        ensure_vertex_access(
            project=self.project,
            location=self.location,
            provider_label="Vertex generation",
        )

        tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name=PatientLookupTool.NAME,
                    description=PatientLookupTool.DESCRIPTION,
                    parameters=PatientLookupTool.PARAMETERS,
                )
            ]
        )
        prompt = (
            "You are orchestrating the clinical assessment workflow. "
            f"The user requested patient ID {requested_patient_id}. "
            f"Call {PatientLookupTool.NAME} exactly once with the patient ID that should be retrieved. "
            "Do not answer in natural language."
        )

        try:
            vertexai.init(project=self.project, location=self.location)
            model = GenerativeModel(self.model_name)
            response = model.generate_content(prompt, tools=[tool])
            payload = self._extract_named_function_call(response=response, expected_name=PatientLookupTool.NAME)
            return PatientLookupPlan.model_validate(payload)
        except (ProviderAuthenticationError, ProviderConfigurationError, ProviderServiceError):
            raise
        except ValidationError as exc:
            raise ProviderServiceError(f"Vertex generation returned an invalid patient lookup call: {exc}") from exc
        except Exception as exc:
            raise wrap_vertex_error(
                provider_label="Vertex generation",
                model_name=self.model_name,
                project=self.project,
                location=self.location,
                exc=exc,
            ) from exc

    def _generate_assessment_vertex(
        self,
        *,
        patient: PatientRecord,
        chunks: list[RetrievedChunk],
    ) -> AssessmentDraft:
        ensure_vertex_access(
            project=self.project,
            location=self.location,
            provider_label="Vertex generation",
        )

        evidence_block = "\n".join(
            f"- [p.{chunk.page} {chunk.section or 'section_unknown'}] {chunk.document[:320]}"
            for chunk in chunks[: min(5, len(chunks))]
        )
        tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="submit_assessment",
                    description="Return the grounded NG12 assessment result.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "recommendation": {
                                "type": "string",
                                "enum": [
                                    "urgent_referral",
                                    "urgent_investigation",
                                    "no_urgent_action",
                                    "insufficient_evidence",
                                ],
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation grounded only in the provided evidence.",
                            },
                            "matched_criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific patient findings supported by the evidence.",
                            },
                        },
                        "required": ["recommendation", "reasoning", "matched_criteria"],
                    },
                )
            ]
        )
        prompt = (
            "You are a clinical decision support assistant operating over NICE NG12 evidence.\n\n"
            f"Patient summary:\n{self._format_patient_summary(patient)}\n\n"
            f"Retrieved NG12 evidence:\n{evidence_block}\n\n"
            "Choose exactly one recommendation:\n"
            "- urgent_referral\n"
            "- urgent_investigation\n"
            "- no_urgent_action\n"
            "- insufficient_evidence\n\n"
            "Rules:\n"
            "- Use only the retrieved NG12 evidence.\n"
            "- Do not invent thresholds, durations, or pathways.\n"
            "- Put only patient-specific supported findings in matched_criteria.\n"
            "- If evidence is weak or conflicting, choose insufficient_evidence.\n"
            "Call submit_assessment exactly once and do not return natural language."
        )

        try:
            vertexai.init(project=self.project, location=self.location)
            model = GenerativeModel(self.model_name)
            response = model.generate_content(prompt, tools=[tool])
            payload = self._extract_named_function_call(response=response, expected_name="submit_assessment")
            return AssessmentDraft.model_validate(payload)
        except (ProviderAuthenticationError, ProviderConfigurationError, ProviderServiceError):
            raise
        except ValidationError as exc:
            raise ProviderServiceError(f"Vertex generation returned an invalid assessment payload: {exc}") from exc
        except Exception as exc:
            raise wrap_vertex_error(
                provider_label="Vertex generation",
                model_name=self.model_name,
                project=self.project,
                location=self.location,
                exc=exc,
            ) from exc

    @staticmethod
    def _generate_mock(system_prompt: str, user_prompt: str) -> str:
        preview = user_prompt.strip().splitlines()[0][:220]
        return (
            "[MOCK_LLM] Grounded response generated in mock mode. "
            f"Input preview: {preview}"
        )

    @staticmethod
    def _generate_assessment_mock(*, patient: PatientRecord, chunks: list[RetrievedChunk]) -> AssessmentDraft:
        evidence_text = " ".join(f"{chunk.document} {chunk.excerpt}" for chunk in chunks).lower()
        supported_findings = sorted({symptom for symptom in patient.symptoms if symptom.lower() in evidence_text})

        # Mock mode stays deterministic for local/offline development while still consuming retrieved evidence.
        if any(symptom in supported_findings for symptom in ["unexplained hemoptysis", "visible haematuria", "unexplained breast lump"]):
            recommendation = "urgent_referral"
        elif any(symptom in supported_findings for symptom in ["dysphagia", "persistent hoarseness", "iron-deficiency anaemia"]):
            recommendation = "urgent_investigation"
        elif supported_findings:
            recommendation = "no_urgent_action"
        else:
            recommendation = "insufficient_evidence"

        if recommendation == "insufficient_evidence":
            reasoning = "Retrieved NG12 evidence did not clearly support a pathway recommendation for this patient."
        else:
            criteria_text = ", ".join(supported_findings) if supported_findings else "the retrieved findings"
            reasoning = (
                "Mock assessment mode found NG12 evidence supporting "
                f"{criteria_text}, which maps to {recommendation}."
            )

        return AssessmentDraft(
            recommendation=recommendation,
            reasoning=reasoning,
            matched_criteria=supported_findings,
        )

    @staticmethod
    def _extract_named_function_call(*, response: object, expected_name: str) -> dict[str, object]:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call is None:
                    continue
                if getattr(function_call, "name", None) != expected_name:
                    continue
                args = getattr(function_call, "args", {})
                return LLMClient._normalize_value(args)

        raise ProviderServiceError(f"Vertex generation did not return the required function call: {expected_name}.")

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): LLMClient._normalize_value(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [LLMClient._normalize_value(item) for item in value]
        return value

    @staticmethod
    def _format_patient_summary(patient: PatientRecord) -> str:
        return (
            f"Patient ID: {patient.patient_id}\n"
            f"Name: {patient.name}\n"
            f"Age: {patient.age}\n"
            f"Gender: {patient.gender}\n"
            f"Smoking history: {patient.smoking_history}\n"
            f"Symptoms: {', '.join(patient.symptoms)}\n"
            f"Symptom duration (days): {patient.symptom_duration_days}"
        )
