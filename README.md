# Ask Mirror Talk

A production-ready MVP for a content-grounded Q&A experience on Mirror Talk podcast episodes. The system ingests the podcast RSS feed, transcribes episodes, chunks and indexes content, and serves answers with episode/timestamp references.

## What’s Included
- RSS ingestion with auto-detection of new episodes
- Long-form transcription (faster-whisper)
- Chunking + tagging (topic, emotional tone, growth domain)
- Vector search over chunks (pgvector)
- Grounded Q&A API (no outside content)
- WordPress integration snippet

## Quick Start

### 1) Start Postgres + pgvector
```bash
docker compose up -d
```

### 2) Create the vector extension
```bash
psql "postgresql://mirror:mirror@localhost:5432/mirror_talk" -f scripts/init_db.sql
```

### 3) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional (for transcription and embeddings):
```bash
pip install -e .[transcription,embeddings]
```

### 4) Configure `.env`
```bash
cp .env.example .env
```

Set your RSS feed URL and other settings.

### 5) Run the API
```bash
uvicorn app.api.main:app --reload
```

### 6) Run the ingestion scheduler (separate terminal)
```bash
python -m app.ingestion.scheduler
```

## API

### `POST /ask`
Request:
```json
{"question": "How do I find peace when I'm anxious?"}
```

Response:
```json
{
  "question": "How do I find peace when I'm anxious?",
  "answer": "...",
  "citations": [
    {
      "episode_id": 12,
      "episode_title": "Learning to Sit With Fear",
      "timestamp_start": "0:14:22",
      "timestamp_end": "0:17:45"
    }
  ],
  "latency_ms": 182
}
```

### `POST /ingest`
Manually triggers an ingestion run (useful for testing).

### `GET /admin`
Basic admin dashboard for recent ingestion runs and Q&A logs. Protected by HTTP Basic auth.

## WordPress Integration
Use the assets in `wordpress/` for the Ask Mirror Talk page.

## Guardrails
- Responses are composed only from retrieved Mirror Talk episode chunks.
- No outside knowledge is used.
- Questions that cannot be answered from the content return a respectful fallback.

## Notes
- The default embedding provider is a local deterministic fallback. For higher-quality retrieval, enable `sentence-transformers`.
- This MVP is structured for easy upgrade to hosted LLMs and higher-grade tagging.

## File Layout
- `app/api/` FastAPI app
- `app/ingestion/` RSS + transcription pipeline
- `app/indexing/` chunking + tagging + embeddings
- `app/qa/` retrieval + answer builder
- `wordpress/` front-end assets
