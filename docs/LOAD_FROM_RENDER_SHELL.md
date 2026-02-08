# Load Data from Render Shell

## Problem
External database access is blocked. Need to load data from within Render.

## Solution: Load from Render Shell

**Run this in the Render shell:**

```bash
cd /app

# Run bulk ingestion (will take 5-10 minutes)
python scripts/bulk_ingest.py --no-confirm
```

This will:
1. Fetch RSS feed (3 episodes)
2. Download audio files to container storage
3. Transcribe with Whisper
4. Generate embeddings with local provider
5. Store in database

## Monitor Progress

While it's running, you can check progress in another terminal:

```bash
# Check status (run this periodically):
curl http://localhost:10000/status

# Or from outside:
curl https://ask-mirror-talk-api.onrender.com/status
```

## Expected Output

You should see:
```
Processing episode 1/3: Episode Title
- Downloading audio...
- Transcribing...
- Chunking...
- Generating embeddings...
- Storing in database...
✓ Episode 1 complete (X chunks)

Processing episode 2/3: ...
...
```

## After Completion

Check status:
```bash
curl http://localhost:10000/status
```

Should show:
```json
{
  "status": "ok",
  "episodes": 3,
  "chunks": 240,
  "ready": true
}
```

## Test the API

```bash
curl -X POST http://localhost:10000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics does Mirror Talk discuss?"}'
```

Should return actual citations now!

## Memory Warning

⚠️ **The starter plan (512MB RAM) might run out of memory** during ingestion because:
- API server is running (~150MB)
- Audio download and processing (~100-200MB per episode)
- Whisper model (~140MB)
- Embedding generation (~50MB)

If you see "Killed" or the process dies, that's an OOM error.

## If OOM Occurs

You have a few options:

### Option 1: Temporarily Upgrade Plan
1. Go to Render Dashboard
2. Upgrade to **Standard plan** ($25/month, 2GB RAM)
3. Run ingestion
4. Downgrade back to Starter after data is loaded

### Option 2: Load One Episode at a Time
```bash
# Modify bulk_ingest.py to process 1 episode:
python -c "
from app.core.db import SessionLocal
from app.ingestion.pipeline import run_ingestion
db = SessionLocal()
# This will only process 1 episode
run_ingestion(db, max_episodes=1)
db.close()
"
```

### Option 3: Re-enable External Access
Follow the guide in `ENABLE_EXTERNAL_DB_ACCESS.md` to whitelist your IP again, then load from local machine.

## Recommended Approach

**Just try running it from the shell first:**
```bash
python scripts/bulk_ingest.py --no-confirm
```

If it crashes with OOM, then consider upgrading temporarily or enabling external access.

---

**ACTION: Run the ingestion in the Render shell and monitor progress!**
