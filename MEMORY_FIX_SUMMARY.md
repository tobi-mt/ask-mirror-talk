# Memory Issue Fix Summary

## Problem
Your ask-mirror-talk web service exceeded its 2GB memory limit and failed.

## Root Cause
**Models were being reloaded on every request**, causing memory to accumulate:
- SentenceTransformer model (~90MB) loaded on every `/ask` request
- WhisperModel (~140MB+) loaded on every transcription
- Multiple concurrent requests multiplied memory usage

## Fixes Applied ✅

### 1. **Model Caching** (Most Important)
- **File: `app/indexing/embeddings.py`**
  - Added singleton pattern to cache the SentenceTransformer model
  - Model loads once and is reused across all requests
  
- **File: `app/ingestion/transcription.py`**
  - Added singleton pattern to cache WhisperModel
  - Model loads once per model name

### 2. **Worker Limits**
- **File: `Dockerfile`**
  - Changed from dynamic workers to single worker: `--workers 1`
  - Added concurrency limit: `--limit-concurrency 10`
  - This prevents multiple model instances from loading

### 3. **Garbage Collection**
- **Files: `app/qa/service.py`, `app/ingestion/pipeline.py`**
  - Added explicit `gc.collect()` after heavy operations
  - Helps Python free up memory more aggressively

### 4. **Documentation**
- **File: `docs/MEMORY_OPTIMIZATION.md`**
  - Complete guide for memory optimization
  - Deployment configurations for different memory limits
  
- **File: `scripts/fix_memory.sh`**
  - Quick setup script for memory-optimized configuration

## Expected Memory Usage (After Fix)

| Configuration | Memory Usage |
|---------------|--------------|
| `EMBEDDING_PROVIDER=local` + `WHISPER_MODEL=tiny` | ~300-500MB |
| `EMBEDDING_PROVIDER=sentence_transformers` + `WHISPER_MODEL=tiny` | ~400-700MB |
| `EMBEDDING_PROVIDER=sentence_transformers` + `WHISPER_MODEL=base` | ~500-800MB |

## Deploy the Fix

### Option 1: Quick Deploy (Recommended)
```bash
# Run the fix script
./scripts/fix_memory.sh

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Monitor memory
docker stats
```

### Option 2: Manual Deploy
```bash
# 1. Set environment variables for ultra-low memory
export EMBEDDING_PROVIDER=local
export WHISPER_MODEL=tiny
export MAX_EPISODES_PER_RUN=1

# 2. Rebuild Docker image
docker-compose -f docker-compose.prod.yml build

# 3. Restart service
docker-compose -f docker-compose.prod.yml up -d

# 4. Monitor
docker stats
```

## Additional Recommendations

### For Production Hosting
1. **Separate Services**: Run ingestion/transcription on a separate worker instance
2. **Use Tiny Models**: Set `WHISPER_MODEL=tiny` for lowest memory
3. **Consider External APIs**: For better quality, use OpenAI Whisper API instead of local model
4. **Monitor**: Set up memory alerts before hitting limits

### Environment Variables to Add
```bash
# For minimal memory usage
EMBEDDING_PROVIDER=local
WHISPER_MODEL=tiny
MAX_EPISODES_PER_RUN=1
RATE_LIMIT_PER_MINUTE=10
```

## Testing the Fix

1. **Check service starts**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f app
   ```

2. **Test an API request**:
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "test question"}'
   ```

3. **Monitor memory**:
   ```bash
   docker stats --no-stream
   ```

## If Issues Persist

1. Set `EMBEDDING_PROVIDER=local` (no ML model needed)
2. Disable transcription and run it separately
3. Increase memory limit on your hosting platform
4. Contact me for further optimization

## Files Changed
- ✅ `app/indexing/embeddings.py` - Added model caching
- ✅ `app/ingestion/transcription.py` - Added model caching  
- ✅ `app/qa/service.py` - Added garbage collection
- ✅ `app/ingestion/pipeline.py` - Added garbage collection
- ✅ `Dockerfile` - Optimized worker configuration
- ✅ `docs/MEMORY_OPTIMIZATION.md` - Added documentation
- ✅ `scripts/fix_memory.sh` - Added quick fix script
