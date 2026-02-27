# NG12 RAG Assessment

This repository implements a clinical assessment + chat assistant over NICE NG12 guidance using one shared RAG pipeline.

## Project Structure

- `backend/`: FastAPI service, ingestion script, datasets, tests.
- `frontend/`: React + Vite TypeScript UI with Risk Assessor and Chat tabs.
- `Dockerfile`: Single-image production build serving API + frontend.

## Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) Docker

## Local Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Ingest NG12 PDF

Download the NG12 PDF and place it at `backend/data/ng12.pdf`, then run:

```bash
python backend/scripts/ingest_ng12.py \
  --pdf backend/data/ng12.pdf \
  --persist-dir backend/data/chroma \
  --collection ng12_guideline \
  --provider mock \
  --reset
```

Use `--provider vertex --project <PROJECT> --location <LOCATION>` to use Vertex embeddings.

### 4. Run Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run Frontend

```bash
cd frontend
npm run dev
```

Frontend defaults to same-origin API. For separate dev servers set `VITE_API_BASE_URL`.

## Docker Run

```bash
docker build -t ng12-rag-assessment .
docker run --rm -p 8000:8000 ng12-rag-assessment
```

Or:

```bash
docker compose up --build
```

## API Endpoints

- `GET /healthz`
- `POST /assess`
- `POST /chat`
- `GET /chat/{session_id}/history`
- `DELETE /chat/{session_id}`

### `POST /assess` example

```json
{
  "patient_id": "PT-101",
  "top_k": 5
}
```

### `POST /chat` example

```json
{
  "session_id": "abc123",
  "message": "What symptoms trigger urgent referral for lung cancer?",
  "top_k": 5
}
```

## Testing

```bash
cd backend
pytest
```

## Environment Variables

- `APP_ENV=dev`
- `LLM_PROVIDER=mock|vertex`
- `LLM_MODEL=gemini-1.5-pro`
- `EMBEDDING_PROVIDER=mock|vertex`
- `EMBEDDING_MODEL=text-embedding-004`
- `GOOGLE_CLOUD_PROJECT=<project-id>`
- `GOOGLE_CLOUD_LOCATION=<region>`
- `VECTOR_DB_PATH=backend/data/chroma`
- `VECTOR_COLLECTION=ng12_guideline`
- `PATIENTS_DATA_PATH=backend/data/patients.json`
- `GUIDELINE_RULES_PATH=backend/data/guideline_rules.yml`

## Safety and Grounding

- Responses include citations and a `safety` block.
- Safety validator assigns `allow`, `qualify`, or `abstain`.
- Rule checks run for `/assess` against curated NG12 criteria.
