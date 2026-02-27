import { FormEvent, useEffect, useState } from "react";

import { apiClient, ChatResponse, ChatTurn } from "../api/client";

export function ChatAssistant() {
  const [sessionId, setSessionId] = useState("session-demo");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatTurn[]>([]);
  const [latest, setLatest] = useState<ChatResponse | null>(null);

  useEffect(() => {
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
      <div className="row">
        <label htmlFor="session-id">Session ID</label>
        <input
          id="session-id"
          value={sessionId}
          onChange={(event) => setSessionId(event.target.value)}
          placeholder="session-id"
        />
        <button type="button" onClick={onClear} disabled={loading}>
          Clear Session
        </button>
      </div>

      <div className="chat-window">
        {history.length === 0 ? <p className="muted">No conversation yet.</p> : null}
        {history.map((turn, index) => (
          <div key={`${turn.role}-${index}`} className={`bubble ${turn.role}`}>
            <strong>{turn.role}:</strong> {turn.content}
          </div>
        ))}
      </div>

      <form className="row" onSubmit={onSubmit}>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={3}
          placeholder="Ask about NG12 criteria..."
        />
        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {latest ? (
        <article className="result-card">
          <header className="result-header">
            <h3>Latest Response</h3>
            <span className={`badge ${latest.safety.action}`}>{latest.safety.action.toUpperCase()}</span>
          </header>
          <p>{latest.answer}</p>
          <div className="metrics">
            <span>Groundedness: {latest.safety.groundedness_score.toFixed(2)}</span>
            <span>Coverage: {latest.safety.evidence_coverage.toFixed(2)}</span>
            <span>Rule: {latest.safety.rule_consistency}</span>
          </div>
          <h4>Citations</h4>
          <ul className="citation-list">
            {latest.citations.map((citation) => (
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
