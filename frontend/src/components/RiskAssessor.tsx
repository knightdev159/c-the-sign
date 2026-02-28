import { FormEvent, useState } from "react";

import { apiClient, AssessResponse } from "../api/client";

const SAMPLE_PATIENTS = ["PT-101", "PT-104", "PT-107", "PT-110"];

function formatSnakeCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function renderValues(values: string[]) {
  if (values.length === 0) {
    return <p className="detail-empty">None</p>;
  }

  return (
    <ul className="detail-list">
      {values.map((value) => (
        <li key={value}>{value}</li>
      ))}
    </ul>
  );
}

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
      <form className="control-card stack" onSubmit={onSubmit}>
        <div className="field-header">
          <label htmlFor="patient-id">Patient ID</label>
          <p className="helper-text">
            Start with a seeded case to inspect how structured lookup, retrieval, and safety scoring line up.
          </p>
        </div>

        <div className="input-row">
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

        <div className="chip-row" aria-label="Sample patients">
          {SAMPLE_PATIENTS.map((samplePatientId) => (
            <button
              key={samplePatientId}
              type="button"
              className={samplePatientId === patientId ? "chip-button active" : "chip-button"}
              onClick={() => setPatientId(samplePatientId)}
            >
              {samplePatientId}
            </button>
          ))}
        </div>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <article className="result-card">
          <header className="result-header">
            <div>
              <p className="card-kicker">Assessment Output</p>
              <h3>
                {result.patient_name} ({result.patient_id})
              </h3>
            </div>
            <span className={`badge ${result.safety.action}`}>{result.safety.action.toUpperCase()}</span>
          </header>

          <div className="callout">
            <span className="callout-label">Recommendation</span>
            <strong className="callout-value">{formatSnakeCase(result.recommendation)}</strong>
            <p>{result.reasoning}</p>
          </div>

          {result.matched_criteria.length ? (
            <div className="tag-group">
              {result.matched_criteria.map((criterion) => (
                <span key={criterion} className="info-tag">
                  {criterion}
                </span>
              ))}
            </div>
          ) : null}

          <div className="metric-grid">
            <article className="metric-card">
              <span className="metric-label">Groundedness</span>
              <strong>{result.safety.groundedness_score.toFixed(2)}</strong>
            </article>
            <article className="metric-card">
              <span className="metric-label">Coverage</span>
              <strong>{result.safety.evidence_coverage.toFixed(2)}</strong>
            </article>
            <article className="metric-card">
              <span className="metric-label">Rule Check</span>
              <strong>{formatSnakeCase(result.safety.rule_consistency)}</strong>
            </article>
          </div>

          <div className="detail-grid">
            <article className="detail-card">
              <span className="detail-label">Model</span>
              <strong>{result.model}</strong>
            </article>
            <article className="detail-card">
              <span className="detail-label">Grounded</span>
              <strong>{result.grounded ? "Yes" : "No"}</strong>
            </article>
            <article className="detail-card">
              <span className="detail-label">Safety Action</span>
              <strong>{formatSnakeCase(result.safety.action)}</strong>
            </article>
          </div>

          <div className="detail-grid detail-grid-stacked">
            <article className="detail-card">
              <span className="detail-label">Unsupported Claims</span>
              {renderValues(result.safety.unsupported_claims)}
            </article>
            <article className="detail-card">
              <span className="detail-label">Conflicts</span>
              {renderValues(result.safety.conflicts)}
            </article>
            <article className="detail-card">
              <span className="detail-label">Notes</span>
              {renderValues(result.safety.notes)}
            </article>
          </div>

          <div className="section-headline">
            <h4>Citations</h4>
            <p>Top NG12 passages retrieved for this assessment.</p>
          </div>

          <ul className="citation-list">
            {result.citations.map((citation) => (
              <li key={citation.chunk_id} className="citation-card">
                <span className="citation-label">
                  {citation.source} · p.{citation.page}
                </span>
                <p>{citation.excerpt}</p>
              </li>
            ))}
          </ul>
        </article>
      ) : null}
    </section>
  );
}
