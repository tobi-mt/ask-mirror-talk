# Ingestion Speed-Up Guide

## Current Bottlenecks Identified

### 1. **Sequential Processing** (Biggest Issue)
- Episodes are processed one at a time
- Each episode requires: download → transcribe → chunk → embed → save
- For 10 episodes: ~20-30 minutes each = 3-5 hours total

### 2. **Embedding Per Chunk**
- Each chunk calls `embed_text()` individually
- For 50 chunks/episode: 50 separate model calls
- Can be batched for 10-50x speedup

### 3. **Database Writes**
- Individual commits per chunk
- Can be batched for significant speedup

### 4. **No Progress Tracking**
- Can't tell if ingestion is working or stuck
- No resumability if it fails

## Speed-Up Solutions

### ⚡ Quick Wins (Apply First)

#### 1. Batch Embeddings (10-50x faster)
Instead of embedding chunks one-by-one, batch them together.

#### 2. Batch Database Inserts (5-10x faster)
Use bulk insert instead of individual commits.

#### 3. Add Progress Logging
See what's happening in real-time.

#### 4. Initial Bulk Ingest Script
Process all episodes at once instead of limiting to 3.

### 🚀 Advanced Optimizations

#### 5. Parallel Processing
Process multiple episodes simultaneously (if you have memory).

#### 6. Skip Already Processed
Resume from where you left off if interrupted.

#### 7. Separate Download Phase
Pre-download all audio files, then process.

## Implementation

See the optimized files created:
- `app/ingestion/pipeline_optimized.py` - Faster pipeline with batching
- `scripts/bulk_ingest.py` - Initial bulk ingestion script
- `app/indexing/embeddings.py` - Batch embedding support

## Expected Speed Improvements

| Optimization | Before | After | Speedup |
|--------------|--------|-------|---------|
| Batch Embeddings | 50 calls | 1 call | 10-50x |
| Batch DB Inserts | 50 commits | 1 commit | 5-10x |
| Overall per Episode | ~30 min | ~3-5 min | 6-10x |
| 20 Episodes | 10 hours | 1-2 hours | 5-10x |

## How to Use

### Step 1: Initial Bulk Ingest (First Time)
```bash
# Set unlimited episodes for initial load
docker-compose -f docker-compose.prod.yml run app python scripts/bulk_ingest.py

# Or with worker
docker-compose -f docker-compose.prod.yml run worker python scripts/bulk_ingest.py
```

### Step 2: Check Progress
```bash
# Watch logs
docker-compose -f docker-compose.prod.yml logs -f app

# Or check admin dashboard
curl http://localhost:8000/admin
```

### Step 3: Ongoing Ingestion (Automatic)
The scheduler will pick up new episodes automatically every hour.

## Monitoring Ingestion

### Check Status via API
```bash
curl -X POST http://localhost:8000/ingest
# Returns: {"status": "accepted"}
```

### Check Database
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U mirror -d mirror_talk

# Check episodes
SELECT COUNT(*) FROM episodes;

# Check chunks
SELECT COUNT(*) FROM chunks;

# Check recent runs
SELECT * FROM ingest_runs ORDER BY started_at DESC LIMIT 5;
```

### Verify Website Can Respond
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics do you cover?"}'
```

If you get an answer with citations, ingestion is working! ✅

## Troubleshooting

### "No results found"
- Check if chunks exist: `SELECT COUNT(*) FROM chunks;`
- If 0, ingestion hasn't completed yet
- Run bulk ingest script

### Ingestion Stuck
- Check logs: `docker-compose logs -f app`
- Look for errors in transcription or download
- Try with smaller episodes first

### Out of Memory During Ingestion
- Process one episode at a time: `MAX_EPISODES_PER_RUN=1`
- Use smaller model: `WHISPER_MODEL=tiny`
- Run ingestion on separate worker instance
