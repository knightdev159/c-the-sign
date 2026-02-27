# Submission Checklist

## Core Requirements

- [ ] `POST /assess` returns recommendation + citations + safety block
- [ ] `POST /chat` returns grounded answer + citations + safety block
- [ ] `GET /chat/{session_id}/history` works
- [ ] `DELETE /chat/{session_id}` works
- [ ] `GET /healthz` works

## Data + RAG

- [ ] `patients.json` ingested via repository layer
- [ ] NG12 PDF ingested into Chroma using `backend/scripts/ingest_ng12.py`
- [ ] Shared vector store reused by assess + chat

## Safety

- [ ] Claim extraction + evidence scoring active
- [ ] Rule engine loaded from `backend/data/guideline_rules.yml`
- [ ] Safety gating emits `allow|qualify|abstain`

## Frontend

- [ ] Risk Assessor tab functional
- [ ] Chat tab functional with session history + clear
- [ ] Citations and safety state visible

## Packaging and Docs

- [ ] Single-image Docker build passes
- [ ] README runbook complete
- [ ] `PROMPTS.md` and `CHAT_PROMPTS.md` included
- [ ] Eval harness + `QUALITY_REPORT.md` included
