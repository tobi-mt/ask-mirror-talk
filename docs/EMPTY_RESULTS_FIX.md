# Production Issue: Empty Search Results

## Current Status
✅ **Bug Fix Applied**: The `/ask` endpoint is working without errors!
✅ **Service Responding**: Health check and ask endpoint both work.
❌ **No Results**: Queries return empty citations and generic "could not find" response.

## Root Cause
The production database likely has **no data** OR the **embeddings were created with a different provider** than what's currently configured.

## Quick Diagnostic (Run in Render Shell)

```bash
# Check database status
curl http://localhost:10000/status
```

Expected output should show:
- Episode count
- Chunk count
- If these are 0, database is empty
- If these are > 0, embedding mismatch is the issue

## Solutions

### Solution 1: Check Current Data (Quick)
```bash
# From Render shell:
curl http://localhost:10000/status
```

### Solution 2: Reload Data with Correct Embeddings (Recommended)

The production database may have been loaded with `sentence_transformers` embeddings, but the API is now using `local` embeddings. They're not compatible!

**Option A: From Local Machine (Recommended)**
```bash
# On your local machine:
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Set environment to production with LOCAL embeddings
export DATABASE_URL="postgresql+psycopg://ask_mirror_talk_user:xxx@oregon-postgres.render.com/ask_mirror_talk_db_xxx"
export EMBEDDING_PROVIDER=local

# Clear production data
python scripts/clear_production.py

# Reload with local embeddings
python scripts/bulk_ingest.py --no-confirm
```

**Option B: From Render Shell**
```bash
# In Render shell:
cd /app

# Clear existing data
python -c "
from app.core.db import SessionLocal
from app.storage.models import Episode, Chunk, IngestRun, QALog
db = SessionLocal()
db.query(Chunk).delete()
db.query(Episode).delete()
db.query(IngestRun).delete()
db.commit()
print('Database cleared')
db.close()
"

# Run ingestion (this will take time!)
python scripts/bulk_ingest.py --no-confirm
```

### Solution 3: Check What's in the Database

```bash
# From Render shell:
python -c "
from app.core.db import SessionLocal
from app.storage.models import Episode, Chunk
db = SessionLocal()
episode_count = db.query(Episode).count()
chunk_count = db.query(Chunk).count()
print(f'Episodes: {episode_count}')
print(f'Chunks: {chunk_count}')
if chunk_count > 0:
    # Check embedding dimension
    chunk = db.query(Chunk).first()
    print(f'Embedding dimension: {len(chunk.embedding) if chunk.embedding else 0}')
db.close()
"
```

## Expected Embedding Dimensions
- **local** (SklearnEmbedder): 384 dimensions
- **sentence_transformers**: 384 dimensions (all-MiniLM-L6-v2)

Even though both are 384d, the actual vector values are different between models!

## Quick Test After Data Load

```bash
curl -X POST http://localhost:10000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics does Mirror Talk discuss?"}'
```

Should return actual citations with episode info.

## Current Environment Check

```bash
# From Render shell, check current config:
python -c "
from app.core.config import settings
print(f'Embedding Provider: {settings.embedding_provider}')
print(f'RSS Feed: {settings.rss_feed_url}')
print(f'Database: {settings.database_url[:50]}...')
"
```

## Next Steps

1. **Check status endpoint** to see if data exists
2. **If no data**: Load data with `local` embeddings
3. **If data exists but wrong embeddings**: Clear and reload
4. **Test** the endpoint again
5. **Test** WordPress integration

## WordPress Testing

Once data is loaded, test from WordPress:
1. Go to https://mirrortalkpodcast.com
2. Find the Ask Mirror Talk widget
3. Ask a question
4. Should get a real answer with citations!

---

**ACTION REQUIRED**: Run `curl http://localhost:10000/status` to see if data exists, then decide whether to reload.
