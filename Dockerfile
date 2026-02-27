# syntax=docker/dockerfile:1

FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

COPY backend/pyproject.toml backend/README.md /app/backend/
COPY backend/app /app/backend/app
COPY backend/scripts /app/backend/scripts
COPY backend/data /app/backend/data

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /app/backend

COPY --from=frontend-builder /frontend/dist /app/backend/app/static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
