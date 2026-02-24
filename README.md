# Ask Mirror Talk

A production-ready MVP for a content-grounded Q&A experience on Mirror Talk podcast episodes. The system ingests the podcast RSS feed, transcribes episodes, chunks and indexes content, and serves answers with episode/timestamp references.

## Features

- RSS ingestion with auto-detection of new episodes
- Transcription via OpenAI Whisper API or faster-whisper (local)
- Chunking + tagging (topic, emotional tone, growth domain)
- Vector search over chunks (pgvector + MMR diversity)
- OpenAI GPT-powered answer generation with basic fallback
- Smart episode citations with audio timestamps
- WordPress widget with inline audio player
- Admin dashboard with analytics
- Citation click tracking & user feedback

## Quick Start

### 1. Start Postgres + pgvector
```bash
docker compose up -d
```

### 2. Create the vector extension
```bash
psql "postgresql://mirror:mirror@localhost:5432/mirror_talk" -f scripts/init_db.sql
```

### 3. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env — set RSS_URL, OPENAI_API_KEY, DATABASE_URL, etc.
```

### 5. Run the API
```bash
uvicorn app.api.main:app --reload
```

### 6. Run the ingestion scheduler (separate terminal)
```bash
python -m app.ingestion.scheduler
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ask` | Ask a question — returns answer + citations |
| `POST` | `/ingest` | Trigger a background ingestion run |
| `GET` | `/health` | Health check |
| `GET` | `/status` | System status (episodes, chunks, latest run) |
| `GET` | `/admin` | Admin dashboard (HTTP Basic auth) |
| `GET` | `/api/analytics/summary` | Analytics summary (last N days) |
| `GET` | `/api/analytics/episodes` | Episode-level analytics |
| `POST` | `/api/citation/click` | Track citation click |
| `POST` | `/api/feedback` | Submit user feedback |

### Example: `POST /ask`
```json
// Request
{"question": "How do I find peace when I'm anxious?"}

// Response
{
  "question": "How do I find peace when I'm anxious?",
  "answer": "...",
  "citations": [
    {
      "episode_id": 12,
      "episode_title": "Learning to Sit With Fear",
      "timestamp_start": "0:14:22",
      "timestamp_end": "0:17:45",
      "audio_url": "https://...",
      "text": "..."
    }
  ],
  "latency_ms": 182,
  "qa_log_id": 42
}
```

## Project Structure

```
app/
├── api/            # FastAPI application & endpoints
│   └── main.py
├── core/           # Config, database, logging
│   ├── config.py
│   ├── db.py
│   └── logging.py
├── indexing/       # Chunking, tagging, embeddings
│   ├── chunking.py
│   ├── embeddings.py
│   └── tagging.py
├── ingestion/      # RSS feed, audio download, transcription
│   ├── audio.py
│   ├── pipeline.py
│   ├── pipeline_optimized.py
│   ├── rss.py
│   ├── scheduler.py
│   ├── transcription.py
│   └── transcription_openai.py
├── qa/             # Question answering & citations
│   ├── answer.py
│   ├── retrieval.py
│   ├── service.py
│   └── smart_citations.py
└── storage/        # SQLAlchemy models & repository
    ├── models.py
    └── repository.py

wordpress/astra/    # WordPress theme integration
├── ask-mirror-talk.php
├── ask-mirror-talk.js
├── ask-mirror-talk.css
└── INSTALL.md

scripts/            # Utility & deployment scripts
docs/archive/       # Historical notes & fix documentation
```

## Deployment

### Railway (recommended)
See [`docs/archive/RAILWAY_QUICKSTART.md`](docs/archive/RAILWAY_QUICKSTART.md) for a step-by-step guide.

- **API service**: Uses `Dockerfile` (lightweight, no ML dependencies)
- **Ingestion worker**: Uses `Dockerfile.worker` (includes ffmpeg, OpenAI SDK)

### Docker Compose (local production)
```bash
docker compose -f docker-compose.prod.yml up --build
```

## WordPress Integration

Upload the files from `wordpress/astra/` to your Astra child theme directory. See [`wordpress/astra/INSTALL.md`](wordpress/astra/INSTALL.md) for details.

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

Key settings:
- `DATABASE_URL` — PostgreSQL connection string
- `RSS_URL` — Podcast RSS feed URL
- `OPENAI_API_KEY` — For transcription & answer generation
- `TRANSCRIPTION_PROVIDER` — `openai` or `faster_whisper`
- `EMBEDDING_PROVIDER` — `openai`, `sentence_transformers`, or `local`
- `ANSWER_GENERATION_PROVIDER` — `openai` or `basic`
