# Memory Optimization Guide

## Problem
The web service was exceeding 2GB memory limit, causing instance failures.

## Root Causes Identified

1. **Model Reloading**: Models were being loaded on every request instead of cached
   - SentenceTransformer model (~90MB) loaded on every `/ask` request
   - WhisperModel (~140MB+) loaded on every transcription
   
2. **Concurrent Requests**: Multiple requests could load multiple model instances simultaneously

3. **No Memory Limits**: No worker count limits or memory guards

## Solutions Implemented

### 1. Model Caching (✅ Applied)
- Added singleton pattern to cache embedding models in `app/indexing/embeddings.py`
- Added singleton pattern to cache Whisper models in `app/ingestion/transcription.py`
- Models now load once and are reused across requests

### 2. Worker Configuration
- Limit Uvicorn workers to prevent memory multiplication
- Use `--workers 1` for services with <512MB available memory
- Use `--workers 2` for services with 512MB-2GB memory
- Configure `--limit-concurrency` to prevent request pile-up

### 3. Separate Worker Process
- Keep transcription/ingestion separate from API service
- Use `Dockerfile.worker` for background tasks
- API service only handles lightweight Q&A

### 4. Memory-Efficient Settings
- Use smaller models when possible:
  - Whisper: `tiny` or `base` instead of `small/medium`
  - Consider using `local` embedding provider for ultra-low memory
  
### 5. Garbage Collection
- Add explicit garbage collection after heavy operations
- Clear model caches if needed

## Deployment Configuration

### For Services <512MB Memory
```bash
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "10"]
```

### For Services 512MB-2GB Memory
```bash
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--limit-concurrency", "20"]
```

### For Services >2GB Memory
```bash
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--limit-concurrency", "50"]
```

## Environment Variables to Set

```bash
# Use lightweight embedding
EMBEDDING_PROVIDER=local

# Or use sentence_transformers with caching
EMBEDDING_PROVIDER=sentence_transformers

# Use smallest Whisper model
WHISPER_MODEL=tiny

# Limit ingestion batch size
MAX_EPISODES_PER_RUN=1
```

## Monitoring

Monitor memory usage with:
```bash
# Check current memory
docker stats

# Check process memory
ps aux | grep uvicorn
```

## Quick Fixes

If memory issues persist:
1. Set `EMBEDDING_PROVIDER=local` (no ML model needed)
2. Set `WHISPER_MODEL=tiny` (smallest Whisper model)
3. Reduce `--workers` to 1
4. Add `--limit-concurrency 5` to Uvicorn
5. Separate ingestion to a worker service
