# NG12 Assessment Guide

## 1. Purpose of This Document

This guide is for presentation and interview discussion.
It explains:

1. The **main specification** from the technical assessment.
2. How this codebase satisfies each requirement.
3. What was added **beyond** the minimum spec to create more hiring impact.

---

## 2. Main Specification (From Assessment)

The assignment has two major parts using one shared RAG pipeline.

### Part 1: Clinical Decision Support (`/assess`)

Required:

1. Input patient ID.
2. Retrieve structured patient data from `patients.json`.
3. Retrieve relevant NG12 guideline context from vector store.
4. Produce recommendation (`urgent_referral`, `urgent_investigation`, etc.) with citations.
5. Serve via FastAPI and provide minimal UI.

### Part 2: Conversational Chat (`/chat`)

Required:

1. Multi-turn chat over the same NG12 vector store used in Part 1.
2. Grounded answers with citations.
3. Optional history and clear-session endpoints.
4. Refuse or qualify when evidence is insufficient.

### Delivery Requirements

1. Dockerized service.
2. Prompt documentation.
3. README runbook.
4. Working frontend for both workflows.

---

## 3. Implementation Mapping (Spec -> Code)

### API Layer

1. `GET /healthz` -> `backend/app/api/routes/health.py`
2. `POST /assess` -> `backend/app/api/routes/assess.py`
3. `POST /chat` -> `backend/app/api/routes/chat.py`
4. `GET /chat/{session_id}/history` -> `backend/app/api/routes/chat.py`
5. `DELETE /chat/{session_id}` -> `backend/app/api/routes/chat.py`

### Structured Data Retrieval

1. Dataset: `backend/data/patients.json`
2. Model: `backend/app/domain/patient.py`
3. Repository: `backend/app/storage/patient_repository.py`

### Shared RAG Pipeline

1. Ingestion script: `backend/scripts/ingest_ng12.py`
2. Vector DB access: `backend/app/services/vector_store.py`
3. Embeddings: `backend/app/services/embedding_client.py`
4. LLM generation: `backend/app/services/llm_client.py`
5. Shared dependency composition: `backend/app/core/dependencies.py`

### Assessment Workflow

1. Agent: `backend/app/services/decision_agent.py`
2. Schemas: `backend/app/schemas/assess.py`

### Chat Workflow

1. Agent: `backend/app/services/chat_agent.py`
2. Session memory: `backend/app/storage/session_memory.py`
3. Schemas: `backend/app/schemas/chat.py`

### Frontend

1. App shell/tab switch: `frontend/src/App.tsx`
2. Risk assessor tab: `frontend/src/components/RiskAssessor.tsx`
3. Chat tab: `frontend/src/components/ChatAssistant.tsx`
4. API client: `frontend/src/api/client.ts`

### Packaging and Docs

1. Docker: `Dockerfile`, `docker-compose.yml`
2. Main runbook: `README.md`
3. Prompt docs: `PROMPTS.md`, `CHAT_PROMPTS.md`

---

## 4. What Was Added Beyond the Main Spec

These items are additional value that can be highlighted to hiring managers.

### A) Clinical Safety Layer (Major Value Add)

Files:

1. `backend/app/services/safety_scoring.py`
2. `backend/app/services/rule_engine.py`
3. `backend/app/services/safety_validator.py`
4. `backend/data/guideline_rules.yml`

What it adds:

1. Claim extraction from generated text.
2. Evidence coverage scoring against retrieved chunks.
3. Rule-based recommendation consistency checks.
4. Safety gate outcome: `allow`, `qualify`, or `abstain`.

Why this is impactful:

1. Demonstrates safety-first design.
2. Shows deterministic controls around LLM behavior.
3. Reduces hallucination risk in clinical messaging.

### B) Structured Safety Output Contract

Added `safety` block in both `/assess` and `/chat` responses:

1. `action`
2. `groundedness_score`
3. `evidence_coverage`
4. `rule_consistency`
5. `unsupported_claims`
6. `conflicts`
7. `notes`

Why this helps:

1. Makes model behavior auditable.
2. Enables easy evaluation dashboards later.

### C) Evaluation Harness

Files:

1. `backend/scripts/run_eval.py`
2. `backend/eval_cases.json`
3. `QUALITY_REPORT.md`

What it adds:

1. Repeatable scenario-based API evaluation.
2. Metrics for pass rate, citation presence, groundedness, abstain rate.
3. Foundation for CI quality gates.

### D) Release/Presentation Artifacts

Files:

1. `.env.example`
2. `backend/http_examples.http`
3. `SUBMISSION_CHECKLIST.md`

What it adds:

1. Faster demo preparation.
2. Cleaner reviewer onboarding.
3. Consistent submission quality.

---

## 5. End-to-End Architecture (How to Explain It)

Use this narrative in presentation:

1. **Ingest once**: NG12 PDF is parsed, chunked, embedded, and stored in Chroma.
2. **Assess path**: patient ID -> structured data lookup -> shared retrieval -> grounded reasoning -> safety gate -> response with citations.
3. **Chat path**: session message + memory context -> shared retrieval -> grounded answer -> safety gate -> response with citations.
4. **Single source of truth**: both workflows use the same vector collection and citation metadata model.

---

## 6. Suggested Presentation Flow (10-15 min)

### Slide 1: Problem and Objective

1. Clinical decisions need both structured patient facts and guideline evidence.
2. Goal: one RAG pipeline powering deterministic and conversational modes.

### Slide 2: Core Architecture

1. FastAPI backend.
2. Shared Chroma vector store.
3. Vertex/mock model abstraction.
4. React UI with two tabs.

### Slide 3: Main Spec Coverage

1. Show endpoint list.
2. Show sample `/assess` and `/chat` outputs with citations.
3. Show conversation history endpoint and clear endpoint.

### Slide 4: Differentiator (Safety Validator)

1. Explain claim extraction + evidence coverage.
2. Explain rule checks.
3. Explain `allow/qualify/abstain` gate.

### Slide 5: Measurability and Quality

1. Show eval harness and metrics.
2. Show how this supports regression testing.

### Slide 6: Tradeoffs and Next Steps

1. In-memory chat storage is take-home friendly but not persistent.
2. Rule set currently curated and can be expanded.
3. Safety scoring can evolve toward semantic verification.

---

## 7. Demo Script (Live)

1. Call `/healthz`.
2. Run `/assess` for `PT-101`.
3. Highlight recommendation, citations, safety block.
4. Ask `/chat` question about referral criteria.
5. Ask follow-up question using same session.
6. Show `/chat/{session_id}/history`.
7. Clear session and show empty history.

---

## 8. Key Talking Points for Hiring Manager

1. The base assignment is fully covered across API, UI, Docker, and docs.
2. The strongest extra feature is a **clinical safety gate** with explicit abstain behavior.
3. The system is designed for extension (provider abstraction, rule expansion, eval harness).
4. The project is not only a demo; it is observable, testable, and explainable.

---

## 9. Recommended Future Improvements (If Asked)

1. Persist chat memory in Redis/SQLite for production.
2. Replace lexical evidence scoring with semantic entailment checks.
3. Add per-criterion confidence calibration.
4. Add authentication/audit logging for compliance contexts.
5. Add CI pipeline that runs ingest smoke test + API eval suite.
