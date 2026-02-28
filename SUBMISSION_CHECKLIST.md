# Submission Checklist

## Core Requirements

- [x] `POST /assess` returns recommendation + citations + safety block
- [x] `POST /chat` returns grounded answer + citations + safety block
- [x] `GET /chat/{session_id}/history` works
- [x] `DELETE /chat/{session_id}` works
- [x] `GET /healthz` works

## Data + RAG

- [x] `patients.json` loaded through the repository layer and exposed via an explicit patient lookup tool in the assessment flow
- [x] NG12 PDF ingested into Chroma using `backend/scripts/ingest_ng12.py`
- [x] Shared vector store reused by assess + chat
- [x] Chroma collection refresh logic handles `--reset` ingestion while the API is running

## Safety

- [x] Claim extraction + evidence scoring active
- [x] Rule engine loaded from `backend/data/guideline_rules.yml`
- [x] Safety gating emits `allow|qualify|abstain`
- [x] Provider configuration and authentication failures return structured API errors instead of raw 500 tracebacks

## Frontend

- [x] Risk Assessor workflow functional
- [x] Chat workflow functional with session history + clear
- [x] Citations and safety state visible
- [x] Assessment and chat are visible together in a single-page workspace for easier inspection
- [x] Frontend reads `VITE_API_BASE_URL` from the shared root `.env`

## Packaging and Docs

- [x] Single-image Docker build configuration present
- [x] README runbook updated for the shared root `.env` workflow
- [x] `PROMPTS.md` and `CHAT_PROMPTS.md` included
- [x] Eval harness + `QUALITY_REPORT.md` included

## Final Manual Checks

- [ ] Re-run live `/assess` and `/chat` smoke tests against the current Vertex project and model access
- [ ] Re-run `python backend/scripts/run_eval.py --base-url http://localhost:8000` and review `backend/eval_report.json`
- [ ] Rebuild Docker image after final content changes
