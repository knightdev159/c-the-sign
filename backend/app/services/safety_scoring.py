"""Safety primitives: claim extraction and evidence scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.rag import RetrievedChunk


@dataclass
class EvidenceScore:
    groundedness_score: float
    evidence_coverage: float
    unsupported_claims: list[str]


class ClaimExtractor:
    """Extract coarse-grained claims from generated text."""

    @staticmethod
    def extract(text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", normalized)
        claims = [sentence.strip().rstrip(".") for sentence in sentences if sentence.strip()]
        return claims


class EvidenceScorer:
    """Approximate claim support by lexical overlap with retrieved evidence."""

    @staticmethod
    def score(claims: list[str], chunks: list[RetrievedChunk]) -> EvidenceScore:
        if not claims:
            return EvidenceScore(groundedness_score=0.0, evidence_coverage=0.0, unsupported_claims=[])

        unsupported: list[str] = []
        for claim in claims:
            if not EvidenceScorer._is_supported(claim, chunks):
                unsupported.append(claim)

        coverage = max(0.0, 1.0 - (len(unsupported) / len(claims)))
        return EvidenceScore(
            groundedness_score=coverage,
            evidence_coverage=coverage,
            unsupported_claims=unsupported,
        )

    @staticmethod
    def _is_supported(claim: str, chunks: list[RetrievedChunk]) -> bool:
        claim_tokens = set(re.findall(r"[a-zA-Z]{3,}", claim.lower()))
        if not claim_tokens:
            return True

        for chunk in chunks:
            chunk_tokens = set(re.findall(r"[a-zA-Z]{3,}", chunk.document.lower()))
            if not chunk_tokens:
                continue
            overlap = len(claim_tokens.intersection(chunk_tokens)) / len(claim_tokens)
            if overlap >= 0.35:
                return True
        return False
