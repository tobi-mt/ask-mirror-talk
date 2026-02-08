FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/

RUN pip install --no-cache-dir -e ".[transcription,embeddings]"

COPY app /app/app
COPY scripts /app/scripts

EXPOSE 8000

# Use Render's PORT environment variable
ENV PORT=8000

# Optimized for memory: single worker with limited concurrency
# Adjust based on available memory:
# - <512MB: --workers 1 --limit-concurrency 5
# - 512MB-2GB: --workers 1 --limit-concurrency 10
# - >2GB: --workers 2 --limit-concurrency 20
CMD uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --limit-concurrency 10
