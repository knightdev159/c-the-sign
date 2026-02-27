"""Safety validator and response gating."""

from __future__ import annotations

from app.domain.patient import PatientRecord
from app.domain.rag import RetrievedChunk
from app.schemas.common import SafetyResponse
from app.services.rule_engine import RuleEngine
from app.services.safety_scoring import ClaimExtractor, EvidenceScorer


class SafetyValidator:
    """Computes safety metrics and selects allow/qualify/abstain gate actions."""

    def __init__(self, rule_engine: RuleEngine, min_allow_coverage: float = 0.8) -> None:
        self._rule_engine = rule_engine
        self._min_allow_coverage = min_allow_coverage

    def validate(
        self,
        *,
        answer_text: str,
        chunks: list[RetrievedChunk],
        mode: str,
        patient: PatientRecord | None = None,
        recommendation: str | None = None,
    ) -> SafetyResponse:
        # Step 1: convert free-text response into atomic claims.
        claims = ClaimExtractor.extract(answer_text)
        # Step 2: estimate how much of the response is supported by retrieved evidence.
        evidence_score = EvidenceScorer.score(claims, chunks)

        conflicts: list[str] = []
        rule_consistency = "unknown"

        if mode == "assess" and patient is not None and recommendation is not None:
            rule_result = self._rule_engine.check_assessment(patient, recommendation)
            rule_consistency = rule_result.rule_consistency
            conflicts = rule_result.conflicts

        action = "allow"
        notes: list[str] = []

        # Gate priority is strict: rule conflicts > unsupported claims > low coverage.
        if conflicts:
            action = "abstain"
            notes.append("Recommendation conflicts with rule checks.")
        elif evidence_score.unsupported_claims:
            action = "abstain"
            notes.append("One or more claims were not supported by retrieved evidence.")
        elif evidence_score.evidence_coverage < self._min_allow_coverage:
            action = "qualify"
            notes.append("Partial evidence coverage; answer should be treated cautiously.")

        return SafetyResponse(
            action=action,
            groundedness_score=evidence_score.groundedness_score,
            evidence_coverage=evidence_score.evidence_coverage,
            rule_consistency=rule_consistency,
            unsupported_claims=evidence_score.unsupported_claims,
            conflicts=conflicts,
            notes=notes,
        )
