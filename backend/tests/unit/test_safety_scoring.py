from app.domain.rag import RetrievedChunk
from app.services.safety_scoring import ClaimExtractor, EvidenceScorer


def test_claim_extractor_splits_sentences() -> None:
    text = "Persistent hoarseness may need referral. Dysphagia can require investigation."
    claims = ClaimExtractor.extract(text)

    assert len(claims) == 2
    assert "Persistent hoarseness" in claims[0]


def test_evidence_scorer_supported_claim() -> None:
    claims = ["Persistent hoarseness requires urgent referral"]
    chunks = [
        RetrievedChunk(
            chunk_id="ng12_0001_00",
            document="NG12 states persistent hoarseness can require urgent referral.",
            source="NG12 PDF",
            page=1,
            section="page_1",
            distance=0.1,
            excerpt="persistent hoarseness can require urgent referral",
        )
    ]

    score = EvidenceScorer.score(claims, chunks)

    assert score.evidence_coverage == 1.0
    assert score.unsupported_claims == []


def test_evidence_scorer_unsupported_claim() -> None:
    claims = ["MRI is mandatory for all patients with fatigue"]
    chunks = [
        RetrievedChunk(
            chunk_id="ng12_0001_00",
            document="Guidance discusses fatigue with additional alarm symptoms.",
            source="NG12 PDF",
            page=1,
            section="page_1",
            distance=0.1,
            excerpt="fatigue with additional alarm symptoms",
        )
    ]

    score = EvidenceScorer.score(claims, chunks)

    assert score.evidence_coverage == 0.0
    assert score.unsupported_claims == claims
