FROM python:3.11-slim

# Force rebuild - updated 2026-02-13 17:30 UTC
ENV REBUILD_DATE=2026-02-13-17-30
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only essential runtime dependencies (minimal for API service)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy dependency files
COPY pyproject.toml README.md /app/

# Install ONLY core API dependencies (no transcription/embedding for API)
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.0 \
    pydantic==2.7.0 \
    pydantic-settings==2.2.0 \
    sqlalchemy==2.0.36 \
    psycopg[binary]==3.1.19 \
    pgvector==0.2.5 \
    alembic==1.13.0 \
    httpx==0.27.0 \
    python-dotenv==1.0.1 \
    openai==1.12.0 \
    && rm -rf /root/.cache/pip /tmp/* /var/tmp/*

# Copy application code
COPY app /app/app
COPY scripts /app/scripts

# Install the package without dependencies
RUN pip install --no-cache-dir --no-deps -e . \
    && rm -rf /root/.cache/pip

# Railway provides PORT environment variable dynamically
EXPOSE 8000

# NO HEALTHCHECK in Dockerfile - configure per-service in Railway Dashboard
# API service should enable healthcheck to /health in Railway settings
# Ingestion service should disable healthcheck in Railway settings

# Use exec form with sh -c to allow environment variable expansion
# Minimal flags for fastest startup
CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
