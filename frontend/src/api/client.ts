export type Citation = {
  source: string;
  page: number;
  chunk_id: string;
  excerpt: string;
};

export type SafetyBlock = {
  action: "allow" | "qualify" | "abstain";
  groundedness_score: number;
  evidence_coverage: number;
  rule_consistency: "pass" | "fail" | "unknown";
  unsupported_claims: string[];
  conflicts: string[];
  notes: string[];
};

export type AssessResponse = {
  patient_id: string;
  patient_name: string;
  recommendation: string;
  reasoning: string;
  matched_criteria: string[];
  citations: Citation[];
  model: string;
  grounded: boolean;
  safety: SafetyBlock;
};

export type ChatResponse = {
  session_id: string;
  answer: string;
  citations: Citation[];
  grounded: boolean;
  safety: SafetyBlock;
};

export type ChatTurn = {
  role: string;
  content: string;
};

export type ChatHistoryResponse = {
  session_id: string;
  history: ChatTurn[];
};

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  assess(patientId: string, topK = 5): Promise<AssessResponse> {
    return request<AssessResponse>("/assess", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId, top_k: topK }),
    });
  },
  chat(sessionId: string, message: string, topK = 5): Promise<ChatResponse> {
    return request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, message, top_k: topK }),
    });
  },
  chatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    return request<ChatHistoryResponse>(`/chat/${sessionId}/history`);
  },
  clearChat(sessionId: string): Promise<{ session_id: string; deleted: boolean }> {
    return request<{ session_id: string; deleted: boolean }>(`/chat/${sessionId}`, {
      method: "DELETE",
    });
  },
};
