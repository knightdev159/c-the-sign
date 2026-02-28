# Backend

FastAPI backend for the NG12 clinical assessment and chat workflows.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cd ..
```

The backend reads configuration from the repo root `.env`.

## Run locally

From the repo root:

```bash
source backend/.venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

## Test

```bash
source backend/.venv/bin/activate
pytest backend/tests
```

## Main pieces

- `app/api/routes/`: FastAPI routes for health, assessment, and chat
- `app/services/decision_agent.py`: assessment flow with patient lookup tool + grounded recommendation generation
- `app/services/chat_agent.py`: conversational RAG flow over the same vector store
- `app/services/vector_store.py`: shared Chroma retrieval layer
- `scripts/ingest_ng12.py`: PDF ingestion and vector index build

See the root [README](/Users/moon/Documents/c-the-sign/README.md) for the full runbook, Docker usage, and environment variable reference.
