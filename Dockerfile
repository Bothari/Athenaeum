# Build the Svelte frontend. adapter-static emits plain files, so Node is a build
# dependency only — nothing from this stage runs at runtime.
FROM node:22-slim AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Overlays the built SPA onto static/: index.html, _app/ and robots.txt. Must come
# after `COPY . .` so it wins over whatever static/ holds in the build context.
COPY --from=frontend /frontend/build/ ./static/

EXPOSE 8741
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8741/healthz || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8741"]
