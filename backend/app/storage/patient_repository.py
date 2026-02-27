"""Structured patient data access layer."""

import json
from pathlib import Path

from app.domain.patient import PatientRecord


class PatientRepository:
    """Loads patient records from a local JSON file."""

    def __init__(self, data_path: Path) -> None:
        self._data_path = data_path
        self._patients = self._load_patients()

    def _load_patients(self) -> dict[str, PatientRecord]:
        payload = json.loads(self._data_path.read_text(encoding="utf-8"))
        patients: dict[str, PatientRecord] = {}
        for item in payload:
            patient = PatientRecord.model_validate(item)
            patients[patient.patient_id] = patient
        return patients

    def get_patient(self, patient_id: str) -> PatientRecord | None:
        return self._patients.get(patient_id)
