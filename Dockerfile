# Stage 1: build the Svelte frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + compiled frontend
FROM python:3.12-slim AS backend
WORKDIR /app

RUN pip install uv --quiet

COPY backend/pyproject.toml .
RUN uv pip install --system -r pyproject.toml

COPY backend/ .

# Pull the compiled frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./static

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
