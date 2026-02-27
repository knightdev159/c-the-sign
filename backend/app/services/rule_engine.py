"""Rule engine for recommendation consistency checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.domain.patient import PatientRecord


@dataclass
class RuleCheckResult:
    rule_consistency: str
    conflicts: list[str]


class RuleEngine:
    """Validates recommendation consistency against curated guideline rules."""

    def __init__(self, rules_path: Path) -> None:
        self._rules = self._load_rules(rules_path)

    @staticmethod
    def _load_rules(rules_path: Path) -> list[dict[str, object]]:
        if not rules_path.exists():
            return []
        payload = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
        return payload.get("rules", [])

    def check_assessment(self, patient: PatientRecord, recommendation: str) -> RuleCheckResult:
        patient_symptoms = {symptom.lower() for symptom in patient.symptoms}
        conflicts: list[str] = []

        for rule in self._rules:
            symptoms = {str(symptom).lower() for symptom in rule.get("symptoms", [])}
            expected = str(rule.get("expected_recommendation", ""))
            if patient_symptoms.intersection(symptoms) and expected and expected != recommendation:
                conflicts.append(
                    f"Rule {rule.get('id')}: expected {expected}, got {recommendation}"
                )

        return RuleCheckResult(
            rule_consistency="fail" if conflicts else "pass",
            conflicts=conflicts,
        )
