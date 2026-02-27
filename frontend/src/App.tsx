import { useMemo, useState } from "react";

type TabId = "assess" | "chat";

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>("assess");

  const tabTitle = useMemo(() => {
    return activeTab === "assess" ? "Risk Assessor" : "Chat Assistant";
  }, [activeTab]);

  return (
    <div className="app-shell">
      <header className="hero">
        <h1>NG12 Clinical Assistant</h1>
        <p>Shared RAG pipeline for decision support and conversational guideline search.</p>
      </header>

      <div className="tabs">
        <button
          className={activeTab === "assess" ? "tab active" : "tab"}
          onClick={() => setActiveTab("assess")}
        >
          Risk Assessor
        </button>
        <button
          className={activeTab === "chat" ? "tab active" : "tab"}
          onClick={() => setActiveTab("chat")}
        >
          Chat
        </button>
      </div>

      <main className="panel">
        <h2>{tabTitle}</h2>
        <p>Frontend scaffold complete. Feature-specific interactions are implemented in subsequent commits.</p>
      </main>
    </div>
  );
}
