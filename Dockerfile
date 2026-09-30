# One container: the API also serves the built frontend. The demo data subset and the fraud model are
# copied from the local, git-ignored build output; they never pass through git (constitution IV).
# The Anthropic key is NOT baked in: it comes from the host's secret store at runtime.

# --- frontend build ---
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- runtime ---
FROM python:3.10-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    WAREHOUSE_DIR=/app/data/warehouse FRONTEND_DIST=/app/frontend/dist HANDOFFS_PATH=/app/data/handoffs.jsonl
WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir -e . && useradd --create-home --uid 10001 app
COPY backend/data/demo-warehouse /app/data/warehouse
COPY backend/data/models/fraud.joblib ./data/models/fraud.joblib
COPY --from=web /web/dist /app/frontend/dist
RUN mkdir -p /app/data && chown -R app /app/data
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health')"
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
