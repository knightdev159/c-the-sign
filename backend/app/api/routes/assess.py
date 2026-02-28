"""Assessment endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.dependencies import get_llm_client, get_patient_lookup_tool, get_safety_validator, get_vector_store
from app.schemas.assess import AssessRequest, AssessResponse
from app.services.decision_agent import DecisionAgent
from app.services.patient_lookup_tool import PatientLookupTool

router = APIRouter(tags=["assessment"])


def get_decision_agent(
    patient_lookup_tool: PatientLookupTool = Depends(get_patient_lookup_tool),
) -> DecisionAgent:
    settings = get_settings()
    return DecisionAgent(
        patient_lookup_tool=patient_lookup_tool,
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
        safety_validator=get_safety_validator(),
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
