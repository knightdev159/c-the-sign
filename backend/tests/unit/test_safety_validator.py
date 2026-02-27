from pathlib import Path

from app.domain.patient import PatientRecord
from app.domain.rag import RetrievedChunk
from app.services.rule_engine import RuleEngine
from app.services.safety_validator import SafetyValidator


def test_safety_validator_abstains_on_rule_conflict() -> None:
    rule_engine = RuleEngine(Path(__file__).resolve().parents[2] / "data" / "guideline_rules.yml")
    validator = SafetyValidator(rule_engine=rule_engine)

    patient = PatientRecord(
        patient_id="PT-101",
        name="John Doe",
        age=55,
        gender="Male",
        smoking_history="Current Smoker",
        symptoms=["unexplained hemoptysis"],
        symptom_duration_days=14,
    )
    chunks = [
        RetrievedChunk(
            chunk_id="ng12_0010_00",
            document="Unexplained hemoptysis should be considered urgent referral.",
            source="NG12 PDF",
            page=10,
            section="page_10",
            distance=0.1,
            excerpt="Unexplained hemoptysis should be considered urgent referral.",
        )
    ]

    safety = validator.validate(
        answer_text="No urgent action is needed for unexplained hemoptysis.",
        chunks=chunks,
        mode="assess",
        patient=patient,
        recommendation="no_urgent_action",
    )

    assert safety.action == "abstain"
    assert safety.rule_consistency == "fail"
    assert safety.conflicts


def test_safety_validator_qualifies_low_coverage() -> None:
    rule_engine = RuleEngine(Path(__file__).resolve().parents[2] / "data" / "guideline_rules.yml")
    validator = SafetyValidator(rule_engine=rule_engine, min_allow_coverage=0.9)

    safety = validator.validate(
        answer_text="   ",
        chunks=[],
        mode="chat",
    )

    assert safety.action == "qualify"
    assert safety.unsupported_claims == []
