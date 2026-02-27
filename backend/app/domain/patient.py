"""Patient domain models."""

from typing import Literal

from pydantic import BaseModel, Field


class PatientRecord(BaseModel):
    """Single patient record from structured dataset."""

    patient_id: str = Field(pattern=r"^PT-\d{3}$")
    name: str
    age: int = Field(ge=0, le=120)
    gender: Literal["Male", "Female"]
    smoking_history: Literal["Current Smoker", "Never Smoked", "Ex-Smoker"]
    symptoms: list[str]
    symptom_duration_days: int = Field(ge=0)
