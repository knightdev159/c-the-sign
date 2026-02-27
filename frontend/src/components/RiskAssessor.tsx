import { FormEvent, useState } from "react";

import { apiClient, AssessResponse } from "../api/client";

export function RiskAssessor() {
  const [patientId, setPatientId] = useState("PT-101");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssessResponse | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    // Reset transient UI state each time the user runs a new assessment.
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.assess(patientId.trim());
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch assessment");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="feature">
      <form className="stack" onSubmit={onSubmit}>
        <label htmlFor="patient-id">Patient ID</label>
        <div className="row">
          <input
            id="patient-id"
            value={patientId}
            onChange={(event) => setPatientId(event.target.value)}
            placeholder="PT-101"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Assessing..." : "Run Assessment"}
          </button>
        </div>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <article className="result-card">
          <header className="result-header">
            <h3>
              {result.patient_name} ({result.patient_id})
            </h3>
            <span className={`badge ${result.safety.action}`}>{result.safety.action.toUpperCase()}</span>
          </header>

          <p>
            <strong>Recommendation:</strong> {result.recommendation}
          </p>
          <p>
            <strong>Reasoning:</strong> {result.reasoning}
          </p>
          {result.matched_criteria.length ? (
            <p>
              <strong>Matched Criteria:</strong> {result.matched_criteria.join(", ")}
            </p>
          ) : null}

          <div className="metrics">
            <span>Groundedness: {result.safety.groundedness_score.toFixed(2)}</span>
            <span>Coverage: {result.safety.evidence_coverage.toFixed(2)}</span>
            <span>Rule: {result.safety.rule_consistency}</span>
          </div>

          <h4>Citations</h4>
          <ul className="citation-list">
            {result.citations.map((citation) => (
              <li key={citation.chunk_id}>
                <strong>
                  [{citation.source} p.{citation.page}]
                </strong>{" "}
                {citation.excerpt}
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}
