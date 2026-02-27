"""Assessment endpoint."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.dependencies import get_llm_client, get_vector_store
from app.schemas.assess import AssessRequest, AssessResponse
from app.services.decision_agent import DecisionAgent
from app.storage.patient_repository import PatientRepository

router = APIRouter(tags=["assessment"])


def get_patient_repository() -> PatientRepository:
    return PatientRepository(data_path=Path(get_settings().patients_data_path))


def get_decision_agent(
    patient_repo: PatientRepository = Depends(get_patient_repository),
) -> DecisionAgent:
    settings = get_settings()
    return DecisionAgent(
        patient_repo=patient_repo,
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
        model_name=settings.llm_model,
    )


@router.post("/assess", response_model=AssessResponse)
def assess_patient(
    payload: AssessRequest,
    agent: DecisionAgent = Depends(get_decision_agent),
) -> AssessResponse:
    try:
        return agent.assess(payload.patient_id, top_k=payload.top_k)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Patient not found: {exc.args[0]}") from exc
