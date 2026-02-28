import { FormEvent, useEffect, useState } from "react";

import { apiClient, ChatResponse, ChatTurn } from "../api/client";

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

export function ChatAssistant() {
  const [sessionId, setSessionId] = useState("session-demo");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [latest, setLatest] = useState<ChatResponse | null>(null);

  useEffect(() => {
    // Session switch should immediately display that session's existing turns.
    void loadHistory(sessionId);
  }, [sessionId]);

  const loadHistory = async (id: string) => {
    try {
      const response = await apiClient.chatHistory(id);
      setHistory(response.history);
    } catch {
      setHistory([]);
    }
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.chat(sessionId.trim(), message.trim());
      setLatest(response);
      setMessage("");
      // Refresh history from API so UI always matches backend source of truth.
      await loadHistory(sessionId.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send chat message");
    } finally {
      setLoading(false);
    }
  };

  const onClear = async () => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.clearChat(sessionId.trim());
      setHistory([]);
      setLatest(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear session");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="feature">
      <div className="control-card">
        <div className="field-header">
          <label htmlFor="session-id">Session ID</label>
          <p className="helper-text">
            Reuse the same session to preserve follow-up context like age thresholds or prior topic focus.
          </p>
        </div>

        <div className="input-row">
          <input
            id="session-id"
            value={sessionId}
            onChange={(event) => setSessionId(event.target.value)}
            placeholder="session-id"
          />
          <button type="button" className="secondary-button" onClick={onClear} disabled={loading}>
            Clear Session
          </button>
        </div>
      </div>

      <div className="chat-window-card">
        <div className="window-header">
          <div>
            <p className="card-kicker">Conversation</p>
            <h3>{sessionId || "Untitled Session"}</h3>
          </div>
          <span className="session-pill">{history.length} turns</span>
        </div>

        <div className="chat-window">
        {history.length === 0 ? <p className="muted">No conversation yet.</p> : null}
        {history.map((turn, index) => (
          <div key={`${turn.role}-${index}`} className={`bubble ${turn.role}`}>
            <span className="bubble-role">{turn.role === "user" ? "Clinician" : "Assistant"}</span>
            <p>{turn.content}</p>
          </div>
        ))}
        </div>
      </div>

      <form className="composer-card" onSubmit={onSubmit}>
        <div className="field-header">
          <label htmlFor="chat-message">Ask a guideline question</label>
          <p className="helper-text">The assistant answers from retrieved NG12 evidence and keeps citations visible.</p>
        </div>

        <div className="composer-row">
          <textarea
            id="chat-message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            rows={3}
            placeholder="Ask about NG12 criteria..."
          />
          <button type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {latest ? (
        <article className="result-card">
          <header className="result-header">
            <div>
              <p className="card-kicker">Latest Response</p>
              <h3>Grounded answer</h3>
            </div>
            <span className={`badge ${latest.safety.action}`}>{latest.safety.action.toUpperCase()}</span>
          </header>

          <div className="callout">
            <span className="callout-label">Answer</span>
            <p>{latest.answer}</p>
          </div>

          <div className="metric-grid">
            <article className="metric-card">
              <span className="metric-label">Groundedness</span>
              <strong>{latest.safety.groundedness_score.toFixed(2)}</strong>
            </article>
            <article className="metric-card">
              <span className="metric-label">Coverage</span>
              <strong>{latest.safety.evidence_coverage.toFixed(2)}</strong>
            </article>
            <article className="metric-card">
              <span className="metric-label">Rule Check</span>
              <strong>{latest.safety.rule_consistency}</strong>
            </article>
          </div>

          <div className="detail-grid">
            <article className="detail-card">
              <span className="detail-label">Session</span>
              <strong>{latest.session_id}</strong>
            </article>
            <article className="detail-card">
              <span className="detail-label">Grounded</span>
              <strong>{latest.grounded ? "Yes" : "No"}</strong>
            </article>
            <article className="detail-card">
              <span className="detail-label">Safety Action</span>
              <strong>{latest.safety.action}</strong>
            </article>
          </div>

          <div className="detail-grid detail-grid-stacked">
            <article className="detail-card">
              <span className="detail-label">Unsupported Claims</span>
              {renderValues(latest.safety.unsupported_claims)}
            </article>
            <article className="detail-card">
              <span className="detail-label">Conflicts</span>
              {renderValues(latest.safety.conflicts)}
            </article>
            <article className="detail-card">
              <span className="detail-label">Notes</span>
              {renderValues(latest.safety.notes)}
            </article>
          </div>

          <div className="section-headline">
            <h4>Citations</h4>
            <p>Supporting excerpts used for the latest answer.</p>
          </div>

          <ul className="citation-list">
            {latest.citations.map((citation) => (
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
