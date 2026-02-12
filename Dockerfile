FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only essential runtime dependencies
# Note: Removed build-essential to save ~500MB
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy dependency files
COPY pyproject.toml README.md /app/

# Install core Python dependencies only (no ML libraries for now)
# This reduces image size from 9GB to ~1.5GB
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
    feedparser==6.0.11 \
    apscheduler==3.10.4 \
    tenacity==8.3.0 \
    python-multipart==0.0.9 \
    python-dotenv==1.0.1 \
    && pip install --no-cache-dir --no-deps faster-whisper==1.0.3 \
    && rm -rf /root/.cache/pip /tmp/* /var/tmp/*

# Copy application code
COPY app /app/app
COPY scripts /app/scripts

# Install the package without dependencies
RUN pip install --no-cache-dir --no-deps -e . \
    && rm -rf /root/.cache/pip

# Railway provides PORT environment variable dynamically
EXPOSE 8000

# Health check - ensure the app starts responding quickly
# Railway has a ~100s healthcheck window, so start-period must be shorter
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Use exec form with sh -c to allow environment variable expansion
# Minimal flags for fastest startup
CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
