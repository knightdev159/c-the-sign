import { ChatAssistant } from "./components/ChatAssistant";
import { RiskAssessor } from "./components/RiskAssessor";

export function App() {
  return (
    <div className="app-shell">
      <header className="hero">
        <p className="eyebrow">Grounded Clinical Workflow</p>
        <h1>NG12 Clinical Assistant</h1>
        <p className="hero-lead">
          Shared RAG pipeline for decision support and conversational guideline search.
        </p>
      </header>

      <main className="workspace-grid">
        <section className="workspace-panel workspace-panel-primary">
          <div className="workspace-header">
            <div>
              <p className="eyebrow panel-eyebrow">Assessment</p>
              <h2>Risk Assessor</h2>
            </div>
            <p className="panel-description">
              Review the patient lookup, recommendation, safety block, and citations in one place.
            </p>
          </div>
          <RiskAssessor />
        </section>

        <section className="workspace-panel">
          <div className="workspace-header">
            <div>
              <p className="eyebrow panel-eyebrow">Conversation</p>
              <h2>Chat Assistant</h2>
            </div>
            <p className="panel-description">
              Keep chat history, the latest answer, and supporting citations visible without switching screens.
            </p>
          </div>
          <ChatAssistant />
        </section>
      </main>
    </div>
  );
}
