"""Structured patient lookup tool used by the assessment agent."""

from __future__ import annotations

from app.domain.patient import PatientRecord
from app.storage.patient_repository import PatientRepository


class PatientLookupTool:
    """Tool facade around the structured patient repository."""

    NAME = "get_patient_record"
    DESCRIPTION = "Fetch a patient record from the structured dataset by patient ID."
    PARAMETERS = {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "Patient identifier in the format PT-101.",
            }
        },
        "required": ["patient_id"],
    }

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._patient_repo = patient_repo

    def invoke(self, patient_id: str) -> PatientRecord | None:
        return self._patient_repo.get_patient(patient_id)
