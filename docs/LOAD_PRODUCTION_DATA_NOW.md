# Production Data Load - Final Steps

## Current Status
- ✅ Bug fix applied and working
- ✅ API responding correctly
- ❌ Database is EMPTY (0 episodes, 0 chunks)
- ⚠️ Previous ingestion started but never completed

## Solution: Load Data from Render Shell

### Option 1: Run Ingestion in Render Shell (Quick Test)

```bash
# In Render shell:
cd /app

# Run bulk ingestion (this will take 5-10 minutes)
python scripts/bulk_ingest.py --no-confirm

# Monitor progress - check status periodically:
curl http://localhost:10000/status
```

**Note:** This will download audio files to the container, which uses ephemeral storage. Fine for testing but data will be lost on restart.

### Option 2: Load from Local Machine (RECOMMENDED)

This is safer and you can monitor it better:

```bash
# On your local machine:
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Make sure .env is set to production
# Check current settings:
cat .env | grep DATABASE_URL
cat .env | grep EMBEDDING_PROVIDER

# Should be:
# DATABASE_URL=postgresql+psycopg://ask_mirror_talk_user:xxx@oregon-postgres.render.com/ask_mirror_talk_db_xxx
# EMBEDDING_PROVIDER=local

# Run the ingestion:
python scripts/bulk_ingest.py --no-confirm
```

### Option 3: Trigger Ingestion via API

```bash
# From anywhere (local or Render shell):
curl -X POST https://ask-mirror-talk-api.onrender.com/ingest

# This runs it in the background
# Check status:
curl https://ask-mirror-talk-api.onrender.com/status
```

**Warning:** This might crash due to memory limits on starter plan.

## Expected Timeline

- **Ingestion Duration**: 5-10 minutes for 3 episodes
- **Episodes**: Should load 3 episodes
- **Chunks**: Should create ~240 chunks

## Monitor Progress

```bash
# Check status every 30 seconds:
watch -n 30 'curl http://localhost:10000/status'

# Or manually:
curl http://localhost:10000/status
```

## After Successful Load

You should see:
```json
{
  "status": "ok",
  "episodes": 3,
  "chunks": 240,
  "ready": true,
  "latest_ingest_run": {
    "status": "completed",
    "started_at": "...",
    "finished_at": "...",
    "message": "Processed 3 episodes successfully"
  }
}
```

## Test After Data Load

```bash
# Test from Render shell:
curl -X POST http://localhost:10000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics does Mirror Talk discuss?"}'

# Should now return actual citations!
```

## Troubleshooting

### If Ingestion Fails (OOM Error)
The starter plan (512MB RAM) might not have enough memory to:
1. Run the API server
2. Download audio files
3. Process transcriptions
4. Generate embeddings

**Solution**: Load data from local machine instead (Option 2 above).

### If Ingestion Hangs
Check logs in Render Dashboard to see what's happening.

## Production Data Load Script

If you want to use the local machine (recommended):

```bash
#!/bin/bash
# Save as: load_production_data.sh

set -e

echo "=== Loading Production Data ==="

# Check environment
if ! grep -q "oregon-postgres.render.com" .env; then
    echo "❌ Error: .env not set to production database"
    exit 1
fi

if ! grep -q "EMBEDDING_PROVIDER=local" .env; then
    echo "❌ Error: EMBEDDING_PROVIDER must be 'local'"
    exit 1
fi

echo "✓ Environment configured for production"

# Clear existing data
echo "Clearing existing data..."
python scripts/clear_production.py

# Load new data
echo "Starting bulk ingestion..."
python scripts/bulk_ingest.py --no-confirm

echo "✓ Done! Check status:"
echo "curl https://ask-mirror-talk-api.onrender.com/status"
```

## Recommended Action

**Run ingestion from your local machine** (safest, won't hit memory limits):

1. Exit Render shell: `exit`
2. On local machine, verify `.env` is set to production
3. Run: `python scripts/bulk_ingest.py --no-confirm`
4. Wait 5-10 minutes
5. Test: `curl https://ask-mirror-talk-api.onrender.com/status`
6. Test ask endpoint
7. Test WordPress integration

---

**Choose your approach and let's get the data loaded!**
