from pathlib import Path

from app.storage.patient_repository import PatientRepository


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "patients.json"


def test_get_existing_patient() -> None:
    repo = PatientRepository(DATA_PATH)
    patient = repo.get_patient("PT-101")

    assert patient is not None
    assert patient.name == "John Doe"
    assert "unexplained hemoptysis" in patient.symptoms


def test_get_missing_patient() -> None:
    repo = PatientRepository(DATA_PATH)

    assert repo.get_patient("PT-999") is None
