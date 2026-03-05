# NG12 Clinical Assistant

FastAPI + React application for two NICE NG12 workflows backed by one shared retrieval pipeline:

- `POST /assess`: assess a patient record from `backend/data/patients.json`
- `POST /chat`: multi-turn guideline Q&A over the same NG12 vector store

The backend returns citations and a `safety` block for both workflows. The frontend exposes both flows in a single UI.

## What is in this repo

- `backend/`: FastAPI app, RAG services, patient dataset, tests, ingestion and evaluation scripts
- `frontend/`: React + Vite TypeScript UI
- `backend/data/chroma/`: committed Chroma database for the NG12 index
- `backend/data/ng12.pdf`: local NG12 PDF used for ingestion/rebuilds
- `Dockerfile`: production image that serves the API and built frontend together

## Prerequisites

- Python `3.11+`
- Node.js `20+`
- npm
- Docker optional

## Quick start

The repository already includes a populated Chroma database in `backend/data/chroma`, so you can start the app without re-ingesting the PDF.

### 1. Configure environment

From the repo root:

```bash
cp .env.example .env
```

The frontend also reads from the repo root `.env`. Set `VITE_API_BASE_URL=http://localhost:8000` there when running the frontend dev server separately from the backend.

### 2. Install backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cd ..
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Run the backend

From the repo root with the backend virtualenv activated:

```bash
source backend/.venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- App root: `http://localhost:8000/`
- OpenAPI docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

### 5. Run the frontend

From `frontend/`:

```bash
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## Docker

For the assessment deliverable, this is the simplest local run path. The container serves both the FastAPI backend and the built frontend from `http://localhost:8000`.

If you want to present the live Vertex-backed flow, set these in the root `.env` first:

```env
LLM_PROVIDER=vertex
EMBEDDING_PROVIDER=vertex
LLM_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=text-embedding-004
GOOGLE_CLOUD_PROJECT=<gcp-project-id>
GOOGLE_CLOUD_LOCATION=<gcp-region>
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/on/your/mac/to/application_default_credentials.json
```

The compose file mounts the host ADC file into the container and rewrites `GOOGLE_APPLICATION_CREDENTIALS` to a valid in-container path.

### Recommended: one command

```bash
docker compose up --build
```

Then open:

- UI + API root: `http://localhost:8000/`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

### Alternative: build + run manually

```bash
docker build -t ng12-clinical-assistant .
docker run --rm \
  --env-file .env \
  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
  -v "$GOOGLE_APPLICATION_CREDENTIALS:/root/.config/gcloud/application_default_credentials.json:ro" \
  -p 8000:8000 \
  ng12-clinical-assistant
```

If you do not want Vertex for a local run, set `LLM_PROVIDER=mock` and `EMBEDDING_PROVIDER=mock` in `.env` before starting the container.

### Docker behavior

- The frontend is prebuilt into the image and served by the FastAPI app.
- `/assess`, `/chat`, `/chat/{session_id}/history`, and `DELETE /chat/{session_id}` are available from the same container.
- The committed Chroma index in `backend/data/chroma` is already included in the image, so ingestion is not required for a first run.
- `docker compose up --build` uses the shared root `.env`, so the same Vertex project/location settings you use locally also apply to the container.

### Optional: rebuild the index before or outside Docker

If you want to regenerate `backend/data/chroma`, run the ingestion script locally first:

```bash
python backend/scripts/ingest_ng12.py \
  --pdf backend/data/ng12.pdf \
  --persist-dir backend/data/chroma \
  --collection ng12_guideline \
  --provider mock \
  --reset
```

Then rebuild the image or rerun Compose.

## Environment variables

Root `.env` values used by the backend:

```env
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
LLM_PROVIDER=mock
LLM_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=mock
EMBEDDING_MODEL=text-embedding-004
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
GOOGLE_APPLICATION_CREDENTIALS=
VECTOR_DB_PATH=backend/data/chroma
VECTOR_COLLECTION=ng12_guideline
PATIENTS_DATA_PATH=backend/data/patients.json
GUIDELINE_RULES_PATH=backend/data/guideline_rules.yml
VITE_API_BASE_URL=http://localhost:8000
```

Notes:

- `mock` mode works offline and is the default local setup.
- If you select `vertex`, the app now fails fast on missing auth or config instead of silently falling back to mock mode.
- The previous Vertex default `gemini-1.5-pro` is retired; use a current model such as `gemini-2.5-flash`.
- Both backend and frontend read `.env` from the repo root.
- Restart the frontend dev server after changing `VITE_API_BASE_URL`.

## API summary

Endpoints:

- `GET /healthz`
- `POST /assess`
- `POST /chat`
- `GET /chat/{session_id}/history`
- `DELETE /chat/{session_id}`

Example assessment request:

```json
{
  "patient_id": "PT-101",
  "top_k": 5
}
```

Example chat request:

```json
{
  "session_id": "demo",
  "message": "What symptoms trigger urgent referral for lung cancer?",
  "top_k": 5
}
```

Useful sample patient IDs in `backend/data/patients.json`:

- `PT-101`
- `PT-102`
- `PT-103`
- `PT-104`
- `PT-105`
- `PT-106`
- `PT-107`
- `PT-108`
- `PT-109`
- `PT-110`

## Rebuild the vector store

You only need this if you want to regenerate `backend/data/chroma` from `backend/data/ng12.pdf` or ingest a different NG12 PDF.

```bash
python backend/scripts/ingest_ng12.py \
  --pdf backend/data/ng12.pdf \
  --persist-dir backend/data/chroma \
  --collection ng12_guideline \
  --provider mock \
  --reset
```

To use Vertex embeddings during ingestion:

1. Authenticate Application Default Credentials for the Vertex SDK:

```bash
gcloud auth application-default login
```

2. Optionally set the active gcloud project:

```bash
gcloud config set project <gcp-project-id>
```

3. Run ingestion:

```bash
python backend/scripts/ingest_ng12.py \
  --pdf backend/data/ng12.pdf \
  --persist-dir backend/data/chroma \
  --collection ng12_guideline \
  --provider vertex \
  --project <gcp-project-id> \
  --location <gcp-region> \
  --reset
```

`gcloud auth login` alone is not enough for the local Vertex SDK flow used here. If you prefer a service account, set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json` instead.

## Chat endpoints

The chat mode uses the same vector index as `/assess`.

- `POST /chat`
- `GET /chat/{session_id}/history`
- `DELETE /chat/{session_id}`

You can exercise them through:

- Swagger UI at `http://localhost:8000/docs`
- [http_examples.http](/Users/moon/Documents/c-the-sign/backend/http_examples.http)

Example:

```json
{
  "session_id": "demo",
  "message": "What symptoms trigger urgent referral for lung cancer?",
  "top_k": 5
}
```

## Testing and evaluation

Backend tests:

```bash
source backend/.venv/bin/activate
pytest backend/tests
```

Scenario evaluation against a running local API:

```bash
source backend/.venv/bin/activate
python backend/scripts/run_eval.py --base-url http://localhost:8000
```

This writes `backend/eval_report.json`.

## Implementation notes

- Both `/assess` and `/chat` use the same Chroma collection and citation model.
- `/assess` starts with an explicit patient lookup tool step, then runs grounded recommendation generation over retrieved NG12 evidence.
- `/chat` stores session history in memory only.
- Session memory keeps up to 20 turns and expires after 24 hours.
- The frontend is a single-page workspace showing both Risk Assessor and Chat Assistant panels together.
- Assessment and chat responses expose safety metadata directly in the UI, including groundedness, conflicts, notes, and citations.

## Limitations

- Chat history is not persistent across process restarts.
- The rule engine is curated and intentionally narrow.
- Mock provider responses are useful for local development but are not clinically meaningful model outputs.
